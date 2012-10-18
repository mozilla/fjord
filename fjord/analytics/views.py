import time
from datetime import timedelta, datetime
from math import floor

from django.shortcuts import render
from django.template.defaultfilters import slugify

from elasticutils.contrib.django import F, es_required_or_50x
from mobility.decorators import mobile_template
from tower import ugettext as _

from fjord.base.helpers import locale_name
from fjord.base.util import smart_int, smart_datetime, epoch_milliseconds
from fjord.feedback.models import SimpleIndex


def counts_to_options(counts, name, display=None, display_map=None,
                      value_map=None, checked=None):
    """Generates a set of option blocks from a set of facet counts.

    One options block represents a set of options to search for, as well as
    the query parameter that can be used to search for that opinion, and the
    friendly name to show the opinion block as.

    For each option the keys mean:
    - `name`: Used to name in the DOM.
    - `display`: Shown to the user.
    - `value`: The value to set the query parameter to in order to search for
      this option.
    - `count`: The facet count of this option.
    - `checked`: Whether the checkbox should start checked.

    :arg counts: A list of tuples of the form (count, item), like from ES.
    :arg name: The name of the search string that corresponds to this block.
        Like "locale" or "platform".
    :arg display: The human friendly title to represent this set of options.
    :arg display_map: Either a dictionary or a function to map items to their
        display names. For a dictionary, the form is {item: display}. For a
        function, the form is lambda item: display_name.
    :arg value_map: Like `display_map`, but for mapping the values that get put
        into the query string for searching.
    :arg checked: Which item should be marked as checked.
    """
    if display is None:
        display = name

    options = {
        'name': name,
        'display': display,
        'options': [],
    }

    # This is used in the loop below, to be a bit neater and so we can do it
    # for both value and display generically.
    def from_map(source, item):
        """Look up an item from a source.

        The source may be a dictionary, a function, or None, in which case the
        item is returned unmodified.

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


day_in_millis = 24 * 60 * 60 * 1000.0


def _zero_fill(start, end, data_sets, spacing=day_in_millis):
    """Given one or more histogram dicts, zero fill them in a range.

    The format of the dictionaries should be {milliseconds: numeric value}. It is
    important that the time points in the dictionary are equally spaced. If they
    are not, extra points will be added.

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

    # `timestamp` is a loop counter that iterates over the timestamps from start
    # to end. It can't just be `timestamp = start`, because then the zeros being
    # adding to the data might not be aligned with the data already in the
    # graph, since we aren't counting by 24 hours, and the data could have a
    # timezone offset.
    #
    # This block picks a time up to `spacing` time after `start` so that it
    # lines up with the data. If there is no data, then we use `stamp =
    # start`, because there is nothing to align with.

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

    # Iterate in the range `start` to `end`, starting from `timestamp`, increasing
    # by `spacing` each time. This ensures there is a data point for each day.
    while timestamp < end_millis:
        for d in data_sets:
            if timestamp not in d:
                d[timestamp] = 0
        timestamp += spacing


@es_required_or_50x(error_template='analytics/es_down.html')
@mobile_template('analytics/{mobile/}dashboard.html')
def dashboard(request, template):
    page = smart_int(request.GET.get('page', 1), 1)
    search_happy = request.GET.get('happy', None)
    search_platform = request.GET.get('platform', None)
    search_locale = request.GET.get('locale', None)
    search_query = request.GET.get('q', None)
    search_date_start = smart_datetime(request.GET.get('date_start', None), fallback=None)
    search_date_end = smart_datetime(request.GET.get('date_end', None), fallback=None)
    selected = request.GET.get('selected', None)

    current_search = {'page': page}

    search = SimpleIndex.search()
    f = F()
    # If search happy is '0' or '1', set it to False or True, respectively.
    search_happy = {'0': False, '1': True}.get(search_happy, None)
    if search_happy in [False, True]:
        f &= F(happy=search_happy)
        current_search['happy'] = int(search_happy)
    if search_platform:
        f &= F(platform=search_platform)
        current_search['platform'] = search_platform
    if search_locale:
        f &= F(locale=search_locale)
        current_search['locale'] = search_locale

    if search_date_start is None and search_date_end is None:
        selected = '7d'

    if search_date_end is None:
        search_date_end = datetime.now()
    if search_date_start is None:
        search_date_start = search_date_end - timedelta(days=7)

    current_search['date_end'] = search_date_end.strftime('%Y-%m-%d')
    # Add one day, so that the search range includes the entire day.
    end = search_date_end + timedelta(days=1)
    # Note 'less than', not 'less than or equal', because of the added day above.
    f &= F(created__lt=end)

    current_search['date_start'] = search_date_start.strftime('%Y-%m-%d')
    f &= F(created__gte=search_date_start)

    if search_query:
        fields = ['text', 'text_phrase', 'fuzzy']
        query = dict(('description__%s' % f, search_query) for f in fields)
        search = search.query(or_=query)
        current_search['q'] = search_query

    search = search.filter(f).order_by('-created')

    facets = search.facet('happy', 'platform', 'locale',
        filtered=bool(f.filters))

    # This loop does two things. First it maps 'T' -> True and 'F' -> False.
    # This is probably something EU should be doing for us. Second, it
    # restructures the data into a more convenient form.
    counts = {'happy': {}, 'platform': {}, 'locale': {}}
    for param, terms in facets.facet_counts().items():
        for term in terms:
            name = term['term']
            if name == 'T':
                name = True
            elif name == 'F':
                name = False

            counts[param][name] = term['count']

    filter_data = [
        counts_to_options(counts['happy'].items(), name='happy',
            display=_('Sentiment'),
            display_map={True: _('Happy'), False: _('Sad')},
            value_map={True: 1, False: 0}, checked=search_happy),
        counts_to_options(counts['platform'].items(),
            name='platform', display=_('Platform'), checked=search_platform),
        counts_to_options(counts['locale'].items(),
            name='locale', display=_('Locale'), checked=search_locale,
            display_map=locale_name)
    ]

    # Histogram data
    happy_data = []
    sad_data = []

    histograms = search.facet_raw(
        happy={
            'date_histogram': {'interval': 'day', 'field': 'created'},
            'facet_filter': (f & F(happy=True)).filters
        },
        sad={
            'date_histogram': {'interval': 'day', 'field': 'created'},
            'facet_filter': (f & F(happy=False)).filters
        },
    ).facet_counts()

    # p['time'] is number of milliseconds since the epoch. Which is
    # convenient, because that is what the front end wants.
    happy_data = dict((p['time'], p['count']) for p in histograms['happy'])
    sad_data = dict((p['time'], p['count']) for p in histograms['sad'])

    _zero_fill(search_date_start, search_date_end, [happy_data, sad_data])
    histogram = [
        {'label': _('Happy'), 'name': 'happy', 'data': sorted(happy_data.items())},
        {'label': _('Sad'), 'name': 'sad', 'data': sorted(sad_data.items())},
    ]

    # Pagination
    if page < 1:
        page = 1
    page_count = 20
    start = page_count * (page - 1)
    end = start + page_count

    search_count = search.count()
    opinion_page = search[start:end]

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
    })
