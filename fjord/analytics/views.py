import json
from collections import defaultdict
from datetime import datetime, timedelta
from math import floor

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import slugify

from elasticutils.contrib.django import F, es_required_or_50x
from funfactory.urlresolvers import reverse
from mobility.decorators import mobile_template
from tower import ugettext as _

from fjord.analytics.forms import OccurrencesComparisonForm
from fjord.analytics.tools import JSONDatetimeEncoder, generate_query_parsed
from fjord.base.helpers import locale_name
from fjord.base.util import (
    analyzer_required,
    check_new_user,
    smart_int,
    smart_datetime,
    epoch_milliseconds,
    Atom1FeedWithRelatedLinks)
from fjord.feedback.models import Response, ResponseMappingType


def counts_to_options(counts, name, display=None, display_map=None,
                      value_map=None, checked=None):
    """Generates a set of option blocks from a set of facet counts.

    One options block represents a set of options to search for, as
    well as the query parameter that can be used to search for that
    opinion, and the friendly name to show the opinion block as.

    For each option the keys mean:
    - `name`: Used to name in the DOM.
    - `display`: Shown to the user.
    - `value`: The value to set the query parameter to in order to
      search for this option.
    - `count`: The facet count of this option.
    - `checked`: Whether the checkbox should start checked.

    :arg counts: A list of tuples of the form (count, item), like from
        ES.
    :arg name: The name of the search string that corresponds to this
        block.  Like "locale" or "platform".
    :arg display: The human friendly title to represent this set of
        options.
    :arg display_map: Either a dictionary or a function to map items
        to their display names. For a dictionary, the form is {item:
        display}. For a function, the form is lambda item:
        display_name.
    :arg value_map: Like `display_map`, but for mapping the values
        that get put into the query string for searching.
    :arg checked: Which item should be marked as checked.
    """
    if display is None:
        display = name

    options = {
        'name': name,
        'display': display,
        'options': [],
    }

    # This is used in the loop below, to be a bit neater and so we can
    # do it for both value and display generically.
    def from_map(source, item):
        """Look up an item from a source.

        The source may be a dictionary, a function, or None, in which
        case the item is returned unmodified.

        """
        if source is None:
            return item
        elif callable(source):
            return source(item)
        else:
            return source[item]

    # Built an option dict for every item.
    for item, count in counts:
        options['options'].append({
            'name': slugify(item),
            'display': from_map(display_map, item),
            'value': from_map(value_map, item),
            'count': count,
            'checked': checked == item,
        })
    options['options'].sort(key=lambda item: item['count'], reverse=True)
    return options


DAY_IN_MILLIS = 24 * 60 * 60 * 1000.0


def _zero_fill(start, end, data_sets, spacing=DAY_IN_MILLIS):
    """Given one or more histogram dicts, zero fill them in a range.

    The format of the dictionaries should be {milliseconds: numeric
    value}. It is important that the time points in the dictionary are
    equally spaced. If they are not, extra points will be added.

    This method works with milliseconds because that is the format
    elasticsearch and Javascript use.

    :arg start: Datetime to start zero filling.
    :arg end: Datetime to stop zero filling at.
    :arg data_sets: A list of dictionaries to zero fill.
    :arg spacing: Number of milliseconds between data points.
    """
    start_millis = epoch_milliseconds(start)
    # Date ranges are inclusive on both ends.
    end_millis = epoch_milliseconds(end) + spacing

    # `timestamp` is a loop counter that iterates over the timestamps
    # from start to end. It can't just be `timestamp = start`, because
    # then the zeros being adding to the data might not be aligned
    # with the data already in the graph, since we aren't counting by
    # 24 hours, and the data could have a timezone offset.
    #
    # This block picks a time up to `spacing` time after `start` so
    # that it lines up with the data. If there is no data, then we use
    # `stamp = start`, because there is nothing to align with.

    # start <= timestamp < start + spacing
    days = [d for d in data_sets if d.keys()]
    if days:
        source = days[0]
        timestamp = source.keys()[0]
        d = floor((timestamp - start_millis) / spacing)
        timestamp -= d * spacing
    else:
        # If there no data, it doesn't matter how it aligns.
        timestamp = start_millis

    # Iterate in the range `start` to `end`, starting from
    # `timestamp`, increasing by `spacing` each time. This ensures
    # there is a data point for each day.
    while timestamp < end_millis:
        for d in data_sets:
            if timestamp not in d:
                d[timestamp] = 0
        timestamp += spacing


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
            link_related=response.url
        )
    return HttpResponse(
        feed.writeString('utf-8'), mimetype='application/atom+xml')


def generate_dashboard_atom_url(request):
    """For a given request, generates the dashboard atom url"""
    qd = request.GET.copy()

    # Remove anything from the querystring that isn't good for a feed:
    # page, start_date, end_date, etc.
    for mem in qd.keys():
        if mem not in ('happy', 'locale', 'platform', 'product',
                       'version', 'q'):
            del qd[mem]

    qd['format'] = 'atom'

    return reverse('dashboard') + '?' + qd.urlencode()


@check_new_user
@es_required_or_50x(error_template='analytics/es_down.html')
@mobile_template('analytics/{mobile/}dashboard.html')
def dashboard(request, template):
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
    search_date_start = smart_datetime(request.GET.get('date_start', None),
                                       fallback=None)
    search_date_end = smart_datetime(request.GET.get('date_end', None),
                                     fallback=None)
    selected = request.GET.get('selected', None)

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

    filter_data = [
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
    ]
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

    _zero_fill(search_date_start, search_date_end, [happy_data, sad_data])
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
        'atom_url': generate_dashboard_atom_url(request)
    })


@check_new_user
@analyzer_required
@es_required_or_50x(error_template='analytics/es_down.html')
@mobile_template('analytics/{mobile/}analytics_dashboard.html')
def analytics_dashboard(request, template):
    return render(request, template)


@check_new_user
@analyzer_required
def analytics_occurrences_comparison(request):
    template = 'analytics/analytics_occurrences_comparison.html'

    first_facet_bi = None
    second_facet_bi = None

    # FIXME - dropdown for products?

    if 'product' in request.GET:
        form = OccurrencesComparisonForm(request.GET)
        if form.is_valid():
            cleaned = form.cleaned_data

            # First item
            first_resp_s = (ResponseMappingType.search()
                            .filter(product=cleaned['product'])
                            .filter(locale__startswith='en'))

            if cleaned['first_version']:
                first_resp_s = first_resp_s.filter(
                    version=cleaned['first_version'])

            if cleaned['first_start_date']:
                first_resp_s = first_resp_s.filter(
                    created__gte=cleaned['first_start_date'])

            if cleaned['first_end_date']:
                first_resp_s = first_resp_s.filter(
                    created__lte=cleaned['first_end_date'])

            if cleaned['first_search_term']:
                first_resp_s = first_resp_s.query(
                    description__text=cleaned['first_search_term'])

            # Have to do raw because we want a size > 10.
            first_resp_s = first_resp_s.facet_raw(
                description_bigrams={
                    'terms': {
                        'field': 'description_bigrams',
                        'size': '20',
                    },
                    'facet_filter': first_resp_s._build_query()['filter']
                }
            )
            first_resp_s = first_resp_s[0:0]

            first_facet = first_resp_s.facet_counts()

            first_facet_bi = first_facet['description_bigrams']
            first_facet_bi = sorted(
                first_facet_bi, key=lambda item: -item['count'])

            if (cleaned['second_version']
                or cleaned['second_search_term']
                or cleaned['second_start_date']):

                second_resp_s = (ResponseMappingType.search()
                                .filter(product=cleaned['product'])
                                .filter(locale__startswith='en'))

                if cleaned['second_version']:
                    second_resp_s = second_resp_s.filter(
                        version=cleaned['second_version'])

                if cleaned['second_start_date']:
                    second_resp_s = second_resp_s.filter(
                        created__gte=cleaned['second_start_date'])

                if cleaned['second_end_date']:
                    second_resp_s = second_resp_s.filter(
                        created__lte=cleaned['second_end_date'])

                if form.cleaned_data['second_search_term']:
                    second_resp_s = second_resp_s.query(
                        description__text=cleaned['second_search_term'])

                # Have to do raw because we want a size > 10.
                second_resp_s = second_resp_s.facet_raw(
                    description_bigrams={
                        'terms': {
                            'field': 'description_bigrams',
                            'size': '20',
                        },
                        'facet_filter': second_resp_s._build_query()['filter']
                    }
                )
                second_resp_s = second_resp_s[0:0]

                second_facet = second_resp_s.facet_counts()

                second_facet_bi = second_facet['description_bigrams']
                second_facet_bi = sorted(
                    second_facet_bi, key=lambda item: -item['count'])

    else:
        form = OccurrencesComparisonForm()

    return render(request, template, {
        'form': form,
        'first_facet_bi': first_facet_bi,
        'second_facet_bi': second_facet_bi,
        'render_time': datetime.now(),
    })


@check_new_user
@analyzer_required
@es_required_or_50x(error_template='analytics/es_down.html')
@mobile_template('analytics/{mobile/}spam_dashboard.html')
def spam_dashboard(request, template):
    return render(request, template)


@check_new_user
@analyzer_required
@es_required_or_50x(error_template='analytics/es_down.html')
def spam_duplicates(request):
    """Shows all duplicate descriptions over the last n days"""
    template = 'analytics/spam_duplicates.html'

    n = 14

    responses = (ResponseMappingType.search()
                 .filter(created__gte=datetime.now() - timedelta(days=n))
                 .values_dict('description', 'happy', 'created', 'locale',
                              'user_agent', 'id')
                 .order_by('created').all())

    total_count = len(responses)

    response_dupes = {}
    for resp in responses:
        response_dupes.setdefault(resp['description'], []).append(resp)

    response_dupes = [
        (key, val) for key, val in response_dupes.items()
        if len(val) > 1
    ]

    # convert the dict into a list of tuples sorted by the number of
    # responses per tuple largest number first
    response_dupes = sorted(response_dupes, key=lambda item: len(item[1]) * -1)

    # duplicate_count -> count
    # i.e. "how many responses had 2 duplicates?"
    summary_counts = defaultdict(int)
    for desc, responses in response_dupes:
        summary_counts[len(responses)] = summary_counts[len(responses)] + 1
    summary_counts = sorted(summary_counts.items(), key=lambda item: item[0])

    return render(request, template, {
        'n': 14,
        'response_dupes': response_dupes,
        'render_time': datetime.now(),
        'summary_counts': summary_counts,
        'total_count': total_count,
    })
