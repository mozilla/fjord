# Note: These views are public with the exception of the response_view
# which has "secure" parts to it in the template.

import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect
)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from elasticsearch import ElasticsearchException
from elasticutils.contrib.django import F, es_required_or_50x
from mobility.decorators import mobile_template
from tower import ugettext as _

from fjord.analytics.tools import (
    counts_to_options,
    zero_fill
)
from fjord.base.helpers import locale_name
from fjord.base.urlresolvers import reverse
from fjord.base.util import (
    analyzer_required,
    check_new_user,
    smart_int,
    smart_date,
    Atom1FeedWithRelatedLinks,
    JSONDatetimeEncoder
)
from fjord.feedback.models import Product, Response, ResponseMappingType
from fjord.journal.models import Record
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

    try:
        prod = Product.objects.get(db_name=response.product)

        if (not prod.on_dashboard
                and (not request.user.is_authenticated()
                     or not request.user.has_perm(
                         'analytics.can_view_dashboard'))):

            # If this is a response for a hidden product and the user
            # isn't in the analytics group, then they can't see it.
            return HttpResponseForbidden()

    except Product.DoesNotExist:
        pass

    mlt = None
    records = None
    errors = []

    if (request.user.is_authenticated()
            and request.user.has_perm('analytics.can_view_dashboard')):

        try:
            # Convert it to a list to force it to execute right now.
            mlt = list(ResponseMappingType.morelikethis(response))
        except ElasticsearchException as exc:
            errors.append('Failed to do morelikethis: %s' % exc)

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
    responses = search.values_dict()[:100]
    json_data = {
        'total': len(responses),
        'results': list(responses),
        'query': search_query
    }
    return HttpResponse(
        json.dumps(json_data, cls=JSONDatetimeEncoder),
        mimetype='application/json')


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
        feed.writeString('utf-8'), mimetype='application/atom+xml')


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

    search = ResponseMappingType.search()
    f = F()
    # If search happy is '0' or '1', set it to False or True, respectively.
    search_happy = {'0': False, '1': True}.get(search_happy, None)
    if search_happy in [False, True]:
        f &= F(happy=search_happy)
        current_search['happy'] = int(search_happy)

    def unknown_to_empty(text):
        """Convert "Unknown" to "" to support old links"""
        return u'' if text.lower() == u'unknown' else text

    if search_platform is not None:
        f &= F(platform=unknown_to_empty(search_platform))
        current_search['platform'] = search_platform
    if search_locale is not None:
        f &= F(locale=unknown_to_empty(search_locale))
        current_search['locale'] = search_locale

    visible_products = [
        prod.encode('utf-8')
        for prod in Product.objects.public().values_list('db_name', flat=True)
    ]

    # This covers the "unknown" product which is also visible.
    visible_products.append('')

    if search_product in visible_products:
        f &= F(product=unknown_to_empty(search_product))
        current_search['product'] = search_product

        if search_version is not None:
            # Note: We only filter on version if we're filtering on
            # product.
            f &= F(version=unknown_to_empty(search_version))
            current_search['version'] = search_version
    else:
        f &= F(product__in=visible_products)

    if search_date_start is None and search_date_end is None:
        selected = '7d'

    if search_date_end is None:
        search_date_end = date.today()
    if search_date_start is None:
        search_date_start = search_date_end - timedelta(days=7)

    current_search['date_end'] = search_date_end.strftime('%Y-%m-%d')
    f &= F(created__lte=search_date_end)

    current_search['date_start'] = search_date_start.strftime('%Y-%m-%d')
    f &= F(created__gte=search_date_start)

    if search_query:
        current_search['q'] = search_query
        search = search.query(description__sqs=search_query)

    if search_bigram is not None:
        f &= F(description_bigrams=search_bigram)
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

    search = search.filter(f).order_by('-created')

    # If the user asked for a feed, give him/her a feed!
    if output_format == 'atom':
        return generate_atom_feed(request, search)

    elif output_format == 'json':
        return generate_json_feed(request, search)

    # Search results and pagination
    if page < 1:
        page = 1
    page_count = 20
    start = page_count * (page - 1)
    end = start + page_count

    search_count = search.count()
    opinion_page = search[start:end]

    # Navigation facet data
    facets = search.facet(
        'happy', 'platform', 'locale', 'product', 'version',
        filtered=bool(search._process_filters(f.filters)))

    # This loop does two things. First it maps 'T' -> True and 'F' ->
    # False.  This is probably something EU should be doing for
    # us. Second, it restructures the data into a more convenient
    # form.
    counts = {
        'happy': {},
        'platform': {},
        'locale': {},
        'product': {},
        'version': {}
    }
    for param, terms in facets.facet_counts().items():
        for term in terms:
            name = term['term']
            if name.upper() == 'T':
                name = True
            elif name.upper() == 'F':
                name = False

            counts[param][name] = term['count']

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
            'note': _('Select product to see version facet')
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

    # Histogram data
    happy_data = []
    sad_data = []

    happy_f = f & F(happy=True)
    sad_f = f & F(happy=False)
    histograms = search.facet_raw(
        happy={
            'date_histogram': {'interval': 'day', 'field': 'created'},
            'facet_filter': search._process_filters(happy_f.filters)
        },
        sad={
            'date_histogram': {'interval': 'day', 'field': 'created'},
            'facet_filter': search._process_filters(sad_f.filters)
        },
    ).facet_counts()

    # p['time'] is number of milliseconds since the epoch. Which is
    # convenient, because that is what the front end wants.
    happy_data = dict((p['time'], p['count']) for p in histograms['happy'])
    sad_data = dict((p['time'], p['count']) for p in histograms['sad'])

    zero_fill(search_date_start, search_date_end, [happy_data, sad_data])
    histogram = [
        {'label': _('Happy'), 'name': 'happy',
         'data': sorted(happy_data.items())},
        {'label': _('Sad'), 'name': 'sad',
         'data': sorted(sad_data.items())},
    ]

    return render(request, template, {
        'opinions': opinion_page,
        'opinion_count': search_count,
        'filter_data': filter_data,
        'histogram': histogram,
        'page': page,
        'prev_page': page - 1 if start > 0 else None,
        'next_page': page + 1 if end < search_count else None,
        'current_search': current_search,
        'selected': selected,
        'atom_url': generate_dashboard_url(request),
    })


@check_new_user
def underconstruction(request):
    return render(request, 'analytics/underconstruction.html')


def generate_totals_histogram(search_date_start, search_date_end,
                              search_query, prod):
    search_date_start = search_date_start - timedelta(days=1)

    search = ResponseMappingType.search()

    if search_query:
        search = search.query(description__sqs=search_query)

    f = F()
    f &= F(product=prod.db_name)

    f &= F(created__gte=search_date_start)
    f &= F(created__lt=search_date_end)

    happy_f = f & F(happy=True)

    totals_histogram = search.facet_raw(
        total={
            'date_histogram': {'interval': 'day', 'field': 'created'},
            'facet_filter': search._process_filters(f.filters)
        },
        happy={
            'date_histogram': {'interval': 'day', 'field': 'created'},
            'facet_filter': search._process_filters(happy_f.filters)
        },
    ).facet_counts()

    totals_data = dict((p['time'], p['count'])
                       for p in totals_histogram['total'])
    zero_fill(search_date_start, search_date_end, [totals_data])
    totals_data = sorted(totals_data.items())

    happy_data = dict((p['time'], p['count'])
                      for p in totals_histogram['happy'])
    zero_fill(search_date_start, search_date_end, [happy_data])
    happy_data = sorted(happy_data.items())

    up_deltas = []
    down_deltas = []
    for i, hap in enumerate(happy_data):
        if i == 0:
            continue

        yesterday = 0
        today = 0

        # Figure out yesterday and today as a percent to one
        # significant digit.
        if happy_data[i-1][1] and totals_data[i-1][1]:
            yesterday = (
                int(happy_data[i-1][1] * 1.0
                    / totals_data[i-1][1] * 1000)
                / 10.0
            )

        if happy_data[i][1] and totals_data[i][1]:
            today = (
                int(happy_data[i][1] * 1.0
                    / totals_data[i][1] * 1000)
                / 10.0
            )

        if (today - yesterday) >= 0:
            up_deltas.append((happy_data[i][0], today - yesterday))
        else:
            down_deltas.append((happy_data[i][0], today - yesterday))

    # Nix the first total because it's not in our date range
    totals_data = totals_data[1:]

    histogram = [
        {
            'name': 'zero',
            'data': [(totals_data[0][0], 0), (totals_data[-1][0], 0)],
            'yaxis': 2,
            'lines': {'show': True, 'fill': False, 'lineWidth': 1,
                      'shadowSize': 0},
            'color': '#dddddd',
        },
        {
            'name': 'total',
            'label': _('Total # responses'),
            'data': totals_data,
            'yaxis': 1,
            'lines': {'show': True, 'fill': False},
            'points': {'show': True},
            'color': '#3E72BF',
        },
        {
            'name': 'updeltas',
            'label': _('Percent change in sentiment upwards'),
            'data': up_deltas,
            'yaxis': 2,
            'bars': {'show': True, 'lineWidth': 3},
            'points': {'show': True},
            'color': '#55E744',
        },
        {
            'name': 'downdeltas',
            'label': _('Percent change in sentiment downwards'),
            'data': down_deltas,
            'yaxis': 2,
            'bars': {'show': True, 'lineWidth': 3},
            'points': {'show': True},
            'color': '#E73E3E',
        }
    ]

    return histogram


def product_dashboard_firefox(request, prod):
    template = 'analytics/product_dashboard_firefox.html'
    current_search = {}

    search_query = request.GET.get('q', None)
    if search_query:
        current_search['q'] = search_query

    search_date_end = smart_date(
        request.GET.get('date_end', None), fallback=None)
    if search_date_end is None:
        search_date_end = date.today()
    current_search['date_end'] = search_date_end.strftime('%Y-%m-%d')

    search_date_start = smart_date(
        request.GET.get('date_start', None), fallback=None)
    if search_date_start is None:
        search_date_start = search_date_end - timedelta(days=7)
    current_search['date_start'] = search_date_start.strftime('%Y-%m-%d')

    histogram = generate_totals_histogram(
        search_date_start, search_date_end, search_query, prod)

    # FIXME: This is lame, but we need to make sure the item we're
    # looking at is the totals.
    assert histogram[1]['name'] == 'total'
    totals_sum = sum([p[1] for p in histogram[1]['data']])

    search = ResponseMappingType.search()
    if search_query:
        search = search.query(description__sqs=search_query)

    base_f = F()
    base_f &= F(product=prod.db_name)
    base_f &= F(created__gte=search_date_start)
    base_f &= F(created__lt=search_date_end)

    search = search.filter(base_f)

    # Figure out the list of platforms and versions for this range.
    plats_and_vers = (search
                      .facet('platform', 'version', size=50)
                      .facet_counts())

    # Figure out the "by platform" histogram
    platforms = [part['term'] for part in plats_and_vers['platform']]
    platform_facet = {}
    for plat in platforms:
        plat_f = base_f & F(platform=plat)
        platform_facet[plat if plat else 'unknown'] = {
            'date_histogram': {'interval': 'day', 'field': 'created'},
            'facet_filter': search._process_filters(plat_f.filters)
        }

    platform_counts = search.facet_raw(**platform_facet).facet_counts()
    platforms_histogram = []
    for key in platform_counts.keys():
        data = dict((p['time'], p['count']) for p in platform_counts[key])

        sum_counts = sum([p['count'] for p in platform_counts[key]])
        if sum_counts < (totals_sum * 0.02):
            # Skip platforms where the number of responses is less than
            # 2% of the total.
            continue

        zero_fill(search_date_start, search_date_end, [data])
        platforms_histogram.append({
            'name': key,
            'label': key,
            'data': sorted(data.items()),
            'lines': {'show': True, 'fill': False},
            'points': {'show': True},
        })

    # Figure out the "by version" histogram
    versions = [part['term'] for part in plats_and_vers['version']]
    version_facet = {}
    for vers in versions:
        vers_f = base_f & F(version=vers)
        version_facet['v' + vers if vers else 'unknown'] = {
            'date_histogram': {'interval': 'day', 'field': 'created'},
            'facet_filter': search._process_filters(vers_f.filters)
        }

    version_counts = search.facet_raw(**version_facet).facet_counts()
    versions_histogram = []
    for key in version_counts.keys():
        data = dict((p['time'], p['count']) for p in version_counts[key])

        sum_counts = sum([p['count'] for p in version_counts[key]])
        if sum_counts < (totals_sum * 0.02):
            # Skip versions where the number of responses is less than
            # 2% of the total.
            continue

        zero_fill(search_date_start, search_date_end, [data])
        versions_histogram.append({
            'name': key,
            'label': key,
            'data': sorted(data.items()),
            'lines': {'show': True, 'fill': False},
            'points': {'show': True},
        })

    return render(request, template, {
        'start_date': search_date_start,
        'end_date': search_date_end,
        'current_search': current_search,
        'platforms_histogram': platforms_histogram,
        'versions_histogram': versions_histogram,
        'histogram': histogram,
        'product': prod
    })


def product_dashboard_generic(request, prod):
    template = 'analytics/product_dashboard.html'
    current_search = {}

    search_query = request.GET.get('q', None)
    if search_query:
        current_search['q'] = search_query

    search_date_end = smart_date(
        request.GET.get('date_end', None), fallback=None)
    if search_date_end is None:
        search_date_end = date.today()
    current_search['date_end'] = search_date_end.strftime('%Y-%m-%d')

    search_date_start = smart_date(
        request.GET.get('date_start', None), fallback=None)
    if search_date_start is None:
        search_date_start = search_date_end - timedelta(days=7)
    current_search['date_start'] = search_date_start.strftime('%Y-%m-%d')

    histogram = generate_totals_histogram(
        search_date_start, search_date_end, search_query, prod)

    return render(request, template, {
        'start_date': search_date_start,
        'end_date': search_date_end,
        'current_search': current_search,
        'histogram': histogram,
        'product': prod
    })


PRODUCT_TO_DASHBOARD = {
    'firefox': product_dashboard_firefox
}


@check_new_user
@es_required_or_50x(error_template='analytics/es_down.html')
def product_dashboard_router(request, productslug):
    prod = get_object_or_404(Product, slug=productslug)
    # FIXME - Some products should never have public dashboards. This
    # should handle that.
    fun = PRODUCT_TO_DASHBOARD.get(productslug, product_dashboard_generic)
    return fun(request, prod)
