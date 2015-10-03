# Note: These views are public with the exception of the response_view
# which has "secure" parts to it in the template.

import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import (
    HttpResponse,
    HttpResponseRedirect
)
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from elasticsearch_dsl import F

from fjord.analytics.utils import counts_to_options
from fjord.base.templatetags.jinja_helpers import locale_name
from fjord.base.urlresolvers import reverse
from fjord.base.utils import (
    analyzer_required,
    check_new_user,
    mobile_template,
    smart_int,
    smart_date,
    Atom1FeedWithRelatedLinks,
    JSONDatetimeEncoder
)
from fjord.feedback.models import Product, Response, ResponseDocType
from fjord.journal.models import Record
from fjord.search.index import es_required_or_50x
from fjord.search.utils import es_error_statsd
from fjord.translations.models import GengoJob, get_translation_systems
from fjord.translations.tasks import create_translation_tasks


@check_new_user
@require_POST
@analyzer_required
def spot_translate(request, responseid):
    # FIXME: This is gengo-machine specific for now.
    resp = get_object_or_404(Response, id=responseid)
    system = request.POST.get('system', None)
    total_jobs = 0
    if system and system in get_translation_systems():
        total_jobs += len(create_translation_tasks(resp, system=system))

    # FIXME: If there's no system specified, we should tell the user
    # something. I'm going to defer fixing that for now since the user
    # would have to be doing "sneaky" things to hit that situation.

    messages.success(request, '%s %s translation jobs added' % (
        total_jobs, system))
    return HttpResponseRedirect(
        reverse('response_view', args=(responseid,)))


@check_new_user
@mobile_template('analytics/{mobile/}response.html')
def response_view(request, responseid, template):
    response = get_object_or_404(Response, id=responseid)

    mlt = None
    records = None
    errors = []

    if (request.user.is_authenticated()
            and request.user.has_perm('analytics.can_view_dashboard')):

        mlt = ResponseDocType.from_obj(response).mlt().execute()

        records = [
            (u'Response records', Record.objects.records(response)),
        ]
        jobs = GengoJob.objects.filter(
            object_id=response.id,
            content_type=ContentType.objects.get_for_model(response)
        )
        for job in jobs:
            records.append(
                (u'Gengo job record {0}'.format(job.id), job.records)
            )

    # We don't pass the response directly to the template and instead
    # do some data tweaks here to make it more palatable for viewing.
    return render(request, template, {
        'errors': errors,
        'response': response,
        'mlt': mlt,
        'records': records,
    })


def generate_json_feed(request, search):
    """Generates JSON feed for first 100 results"""
    search_query = request.GET.get('q', None)
    responses = [resp.to_dict() for resp in search[:100]]
    json_data = {
        'total': len(responses),
        'results': list(responses),
        'query': search_query
    }
    return HttpResponse(
        json.dumps(json_data, cls=JSONDatetimeEncoder),
        content_type='application/json')


def generate_atom_feed(request, search):
    """Generates ATOM feed for first 100 results"""
    search_query = request.GET.get('q', None)

    if search_query:
        title = _(u'Firefox Input: {query}').format(query=search_query)
    else:
        title = _(u'Firefox Input')

    # Build the non-atom dashboard url and maintain all the
    # querystring stuff we have
    dashboard_url = request.build_absolute_uri()
    dashboard_url = dashboard_url.replace('format=atom', '')
    dashboard_url = dashboard_url.replace('&&', '&')
    if dashboard_url.endswith(('?', '&')):
        dashboard_url = dashboard_url[:-1]

    feed = Atom1FeedWithRelatedLinks(
        title=title,
        link=dashboard_url,
        description=_('Search Results From Firefox Input'),
        author_name=_('Firefox Input'),
    )
    for response in search[:100]:
        categories = {
            'sentiment': _('Happy') if response.happy else _('Sad'),
            'platform': response.platform,
            'locale': response.locale
        }
        categories = (':'.join(item) for item in categories.items())

        link_url = reverse('response_view', args=(response.id,))
        link_url = request.build_absolute_uri(link_url)

        feed.add_item(
            title=_('Response id: {id}').format(id=response.id),
            description=response.description,
            link=link_url,
            pubdate=response.created,
            categories=categories,
            link_related=response.url_domain,
        )
    return HttpResponse(
        feed.writeString('utf-8'), content_type='application/atom+xml')


def generate_dashboard_url(request, output_format='atom',
                           viewname='dashboard'):
    """For a given request, generates the dashboard url for the given format

    """
    qd = request.GET.copy()

    # Remove anything from the querystring that isn't good for a feed:
    # page, start_date, end_date, etc.
    for mem in qd.keys():
        if mem not in ('happy', 'locale', 'platform', 'product',
                       'version', 'q'):
            del qd[mem]

    qd['format'] = output_format

    return reverse(viewname) + '?' + qd.urlencode()


@check_new_user
@es_required_or_50x(error_template='analytics/es_down.html')
@es_error_statsd
def dashboard(request):
    template = 'analytics/dashboard.html'

    output_format = request.GET.get('format', None)
    page = smart_int(request.GET.get('page', 1), 1)

    # Note: If we add additional querystring fields, we need to add
    # them to generate_dashboard_url.
    search_happy = request.GET.get('happy', None)
    search_platform = request.GET.get('platform', None)
    search_locale = request.GET.get('locale', None)
    search_product = request.GET.get('product', None)
    search_version = request.GET.get('version', None)
    search_query = request.GET.get('q', None)
    search_date_start = smart_date(
        request.GET.get('date_start', None), fallback=None)
    search_date_end = smart_date(
        request.GET.get('date_end', None), fallback=None)
    search_bigram = request.GET.get('bigram', None)
    selected = request.GET.get('selected', None)

    filter_data = []
    current_search = {'page': page}

    search = ResponseDocType.docs.search()
    f = F()
    # If search happy is '0' or '1', set it to False or True, respectively.
    search_happy = {'0': False, '1': True}.get(search_happy, None)
    if search_happy in [False, True]:
        f &= F('term', happy=search_happy)
        current_search['happy'] = int(search_happy)

    def unknown_to_empty(text):
        """Convert "Unknown" to "" to support old links"""
        return u'' if text.lower() == u'unknown' else text

    if search_platform is not None:
        f &= F('term', platform=unknown_to_empty(search_platform))
        current_search['platform'] = search_platform
    if search_locale is not None:
        f &= F('term', locale=unknown_to_empty(search_locale))
        current_search['locale'] = search_locale

    visible_products = [
        prod.encode('utf-8')
        for prod in Product.objects.public().values_list('db_name', flat=True)
    ]

    # This covers the "unknown" product which is also visible.
    visible_products.append('')

    if search_product in visible_products:
        f &= F('term', product=unknown_to_empty(search_product))
        current_search['product'] = search_product

        if search_version is not None:
            # Note: We only filter on version if we're filtering on
            # product.
            f &= F('term', version=unknown_to_empty(search_version))
            current_search['version'] = search_version
    else:
        f &= F('terms', product=visible_products)

    if search_date_start is None and search_date_end is None:
        selected = '7d'

    if search_date_end is None:
        search_date_end = date.today()
    if search_date_start is None:
        search_date_start = search_date_end - timedelta(days=7)

    # If the start and end dates are inverted, switch them into proper
    # chronoligcal order
    search_date_start, search_date_end = sorted(
        [search_date_start, search_date_end])

    # Restrict the frontpage dashboard to only show the last 6 months
    # of data
    six_months_ago = date.today() - timedelta(days=180)
    search_date_start = max(six_months_ago, search_date_start)
    search_date_end = max(search_date_start, search_date_end)

    current_search['date_end'] = search_date_end.strftime('%Y-%m-%d')
    f &= F('range', created={'lte': search_date_end})

    current_search['date_start'] = search_date_start.strftime('%Y-%m-%d')
    f &= F('range', created={'gte': search_date_start})

    if search_query:
        current_search['q'] = search_query
        search = search.query('simple_query_string', query=search_query,
                              fields=['description'])

    if search_bigram is not None:
        f &= F('terms', description_bigrams=search_bigram)
        filter_data.append({
            'display': _('Bigram'),
            'name': 'bigram',
            'options': [{
                'count': 'all',
                'name': search_bigram,
                'display': search_bigram,
                'value': search_bigram,
                'checked': True
            }]
        })

    search = search.filter(f).sort('-created')

    # If the user asked for a feed, give him/her a feed!
    if output_format == 'atom':
        return generate_atom_feed(request, list(search.execute()))

    elif output_format == 'json':
        return generate_json_feed(request, list(search.execute()))

    # Search results and pagination
    if page < 1:
        page = 1
    page_count = 20
    start = page_count * (page - 1)
    end = start + page_count

    search_count = search.count()
    opinion_page = search[start:end].execute()

    # Add navigation aggregations
    counts = {
        'happy': {},
        'platform': {},
        'locale': {},
        'product': {},
        'version': {}
    }

    for name in counts.keys():
        search.aggs.bucket(name, 'terms', field=name, size=1000)

    happy_sad_filter = request.GET.get('happy', None)

    if happy_sad_filter:
        if happy_sad_filter == '1':
            counts['happy'] = {True: 0}
        elif happy_sad_filter == '0':
            counts['happy'] = {False: 0}
    else:
        counts['happy'] = {True: 0, False: 0}

    if search_platform:
        counts['platform'] = {search_platform: 0}

    if search_locale:
        counts['locale'] = {search_locale: 0}

    if search_product:
        counts['product'] = {search_product: 0}

    if search_version:
        counts['version'] = {search_version: 0}

    results = search.execute()

    # Extract the value and doc_count for the various facets we do
    # faceted navigation on.
    for name in counts.keys():
        buckets = getattr(results.aggregations, name)['buckets']
        for bucket in buckets:
            key = bucket['key']
            # Convert from 'T'/'F' to True/False
            if key in ['T', 'F']:
                key = (key == 'T')
            counts[name][key] = bucket['doc_count']

    def empty_to_unknown(text):
        return _('Unknown') if text == u'' else text

    filter_data.extend([
        counts_to_options(
            counts['happy'].items(),
            name='happy',
            display=_('Sentiment'),
            display_map={True: _('Happy'), False: _('Sad')},
            value_map={True: 1, False: 0},
            checked=search_happy),
        counts_to_options(
            counts['product'].items(),
            name='product',
            display=_('Product'),
            display_map=empty_to_unknown,
            checked=search_product)
    ])
    # Only show the version if we're showing a specific
    # product.
    if search_product:
        filter_data.append(
            counts_to_options(
                counts['version'].items(),
                name='version',
                display=_('Version'),
                display_map=empty_to_unknown,
                checked=search_version)
        )
    else:
        filter_data.append({
            'display': _('Version'),
            'note': _('Select product to see version breakdown')
        })

    filter_data.extend(
        [
            counts_to_options(
                counts['platform'].items(),
                name='platform',
                display=_('Platform'),
                display_map=empty_to_unknown,
                checked=search_platform),
            counts_to_options(
                counts['locale'].items(),
                name='locale',
                display=_('Locale'),
                checked=search_locale,
                display_map=locale_name),
        ]
    )

    return render(request, template, {
        'opinions': opinion_page,
        'opinion_count': search_count,
        'filter_data': filter_data,
        'page': page,
        'prev_page': page - 1 if start > 0 else None,
        'next_page': page + 1 if end < search_count else None,
        'current_search': current_search,
        'selected': selected,
        'atom_url': generate_dashboard_url(request),
    })
