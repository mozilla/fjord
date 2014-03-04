# Note: These views are public with the exception of the response_view
# which has "secure" parts to it in the template.

import json
from datetime import datetime, timedelta

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from elasticutils.contrib.django import F, es_required_or_50x
from funfactory.urlresolvers import reverse
from mobility.decorators import mobile_template
from tower import ugettext as _

from fjord.analytics.tools import (
    JSONDatetimeEncoder,
    generate_query_parsed,
    counts_to_options,
    zero_fill)
from fjord.base.helpers import locale_name
from fjord.base.util import (
    check_new_user,
    smart_int,
    smart_date,
    Atom1FeedWithRelatedLinks)
from fjord.feedback.models import Response, ResponseMappingType


@check_new_user
@mobile_template('analytics/{mobile/}response.html')
def response_view(request, responseid, template):
    response = get_object_or_404(Response, id=responseid)

    # We don't pass the response directly to the template and instead
    # do some data tweaks here to make it more palatable for viewing.
    return render(request, template, {
        'response': response,
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
    """For a given request, generates the dashboard url for the given format"""
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
    if search_product is not None:
        f &= F(product=unknown_to_empty(search_product))
        current_search['product'] = search_product

        if search_version is not None:
            # Note: We only filter on version if we're filtering on
            # product.
            f &= F(version=unknown_to_empty(search_version))
            current_search['version'] = search_version

    if search_date_start is None and search_date_end is None:
        selected = '7d'

    if search_date_end is None:
        search_date_end = datetime.now()
    if search_date_start is None:
        search_date_start = search_date_end - timedelta(days=7)

    current_search['date_end'] = search_date_end.strftime('%Y-%m-%d')
    # Add one day, so that the search range includes the entire day.
    end = search_date_end + timedelta(days=1)
    # Note 'less than', not 'less than or equal', because of the added
    # day above.
    f &= F(created__lt=end)

    current_search['date_start'] = search_date_start.strftime('%Y-%m-%d')
    f &= F(created__gte=search_date_start)

    if search_query:
        current_search['q'] = search_query
        es_query = generate_query_parsed('description', search_query)
        search = search.query_raw(es_query)

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
            if name == 'T':
                name = True
            elif name == 'F':
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
