from django.shortcuts import render
from django.template.defaultfilters import slugify

import pyes
from elasticutils import F
from mobility.decorators import mobile_template
from tower import ugettext as _

from fjord.feedback.models import SimpleIndex
from fjord.base.helpers import locale_name


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


@mobile_template('analytics/{mobile/}dashboard.html')
def dashboard(request, template):
    page = int(request.GET.get('page', 1))
    search_happy = request.GET.get('happy', None)
    search_platform = request.GET.get('platform', None)
    search_locale = request.GET.get('locale', None)
    current_search = {'page': page}
    search = SimpleIndex.search()
    f = F()
    # If search happy is '0' or '1', set it to False or True, respectively.
    search_happy = {'0': False, '1': True}.get(search_happy, None)
    if search_happy in [False, True]:
        f &= F(happy=search_happy)
        current_search['happy'] = search_happy
    if search_platform:
        f &= F(platform=search_platform)
        current_search['platform'] = search_platform
    if search_locale:
        f &= F(locale=search_locale)
        current_search['locale'] = search_locale

    search = search.filter(f).order_by('-created')

    facets = search.facet('happy', 'platform', 'locale',
        filtered=bool(f.filters))

    # This loop does two things. First it maps 'T' -> True and 'F' -> False.
    # This is probably something EU should be doing for us. Second, it
    # restructures the data into a more convenient form.
    counts = {'happy': {}, 'platform': {}, 'locale': {}}
    try:
        for param, terms in facets.facet_counts().items():
            for term in terms:
                name = term['term']
                if name == 'T':
                    name = True
                elif name == 'F':
                    name = False

                counts[param][name] = term['count']
    except (pyes.urllib3.TimeoutError,
            pyes.urllib3.MaxRetryError,
            pyes.exceptions.IndexMissingException,
            pyes.exceptions.ElasticSearchException):

        # TODO: Fix this--we should log an error or show a message or
        # something--anything except an HTTP 500 error on the front
        # page.
        pass

    filter_data = [
        counts_to_options(counts['happy'].items(), name='happy',
            display=_('Sentiment'), display_map={True: 'Happy', False: 'Sad'},
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

    try:
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
        happy_data = [(p['time'], p['count']) for p in histograms['happy']]
        sad_data = [(p['time'], int(p['count'])) for p in histograms['sad']]
    except (pyes.urllib3.TimeoutError,
            pyes.urllib3.MaxRetryError,
            pyes.exceptions.IndexMissingException,
            pyes.exceptions.ElasticSearchException):

        # TODO: Fix this--we should log an error or show a message or
        # something--anything except an HTTP 500 error on the front
        # page.
        pass

    histogram = [
        {'label': 'Happy', 'data': happy_data},
        {'label': 'Sad', 'data': sad_data},
    ]

    # Pagination
    if page < 1:
        page = 1
    page_count = 20
    start = page_count * (page - 1)
    end = start + page_count

    try:
        search_count = search.count()
        opinion_page = search[start:end]
    except (pyes.urllib3.TimeoutError,
            pyes.urllib3.MaxRetryError,
            pyes.exceptions.IndexMissingException,
            pyes.exceptions.ElasticSearchException):

        # TODO: Fix this--we should log an error or show a message or
        # something--anything except an HTTP 500 error on the front
        # page.
        search_count = 0
        opinion_page = []

    return render(request, template, {
        'opinions': opinion_page,
        'opinion_count': search_count,
        'filter_data': filter_data,
        'histogram': histogram,
        'page': page,
        'prev_page': page - 1 if start > 0 else None,
        'next_page': page + 1 if end < search_count else None,
        'current_search': current_search,
    })
