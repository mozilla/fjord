from datetime import datetime, timedelta
import logging

from nose.tools import eq_
from pyelasticsearch.exceptions import Timeout
from pyquery import PyQuery

from fjord.analytics import views
from fjord.analytics.views import counts_to_options, _zero_fill
from fjord.base.tests import TestCase, LocalizingClient, reverse
from fjord.base.util import epoch_milliseconds
from fjord.feedback.tests import simple
from fjord.search.tests import ElasticTestCase


logger = logging.getLogger(__name__)


class TestCountsHelper(TestCase):
    def setUp(self):
        self.counts = [('apples', 5), ('bananas', 10), ('oranges', 6)]

    def test_basic(self):
        """The right options should be set, and the values should be sorted."""
        options = counts_to_options(self.counts, 'fruit', 'Fruit')
        eq_(options['name'], 'fruit')
        eq_(options['display'], 'Fruit')

        eq_(options['options'][0], {
            'name': 'bananas',
            'display': 'bananas',
            'value': 'bananas',
            'count': 10,
            'checked': False,
        })
        eq_(options['options'][1], {
            'name': 'oranges',
            'display': 'oranges',
            'value': 'oranges',
            'count': 6,
            'checked': False,
        })
        eq_(options['options'][2], {
            'name': 'apples',
            'display': 'apples',
            'value': 'apples',
            'count': 5,
            'checked': False,
        })

    def test_map_dict(self):
        options = counts_to_options(self.counts, 'fruit', display_map={
            'apples': 'Apples',
            'bananas': 'Bananas',
            'oranges': 'Oranges',
        })
        # Note that options get sorted by count.
        eq_(options['options'][0]['display'], 'Bananas')
        eq_(options['options'][1]['display'], 'Oranges')
        eq_(options['options'][2]['display'], 'Apples')

    def test_map_func(self):
        options = counts_to_options(self.counts, 'fruit',
            value_map=lambda s: s.upper())
        # Note that options get sorted by count.
        eq_(options['options'][0]['value'], 'BANANAS')
        eq_(options['options'][1]['value'], 'ORANGES')
        eq_(options['options'][2]['value'], 'APPLES')

    def test_checked(self):
        options = counts_to_options(self.counts, 'fruit', checked='apples')
        # Note that options get sorted by count.
        assert not options['options'][0]['checked']
        assert not options['options'][1]['checked']
        assert options['options'][2]['checked']


class TestZeroFillHelper(TestCase):

    def test_zerofill(self):
        start = datetime(2012, 1, 1)
        end = datetime(2012, 1, 7)
        data1 = {
            epoch_milliseconds(datetime(2012, 1, 3)): 1,
            epoch_milliseconds(datetime(2012, 1, 5)): 1,
        }
        data2 = {
            epoch_milliseconds(datetime(2012, 1, 2)): 1,
            epoch_milliseconds(datetime(2012, 1, 5)): 1,
            epoch_milliseconds(datetime(2012, 1, 10)): 1,
        }
        _zero_fill(start, end, [data1, data2])

        for day in range(1, 8):
            millis = epoch_milliseconds(datetime(2012, 1, day))
            assert millis in data1, "Day %s was not zero filled." % day
            assert millis in data2, "Day %s was not zero filled." % day


class TestDashboardView(ElasticTestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(TestDashboardView, self).setUp()
        # Set up some sample data
        # 4 happy, 3 sad.
        # 2 Windows XP, 2 Linux, 1 OS X, 2 Windows 7
        now = datetime.now()
        # The dashboard by default shows the last week of data, so these need
        # to be relative to today. The alternative is that every test gives an
        # explicit date range, and that is annoying and verbose.
        items = [
            (True, 'Windows XP', 'en-US', 'apple', now - timedelta(days=6)),
            (True, 'Windows 7', 'es', 'banana', now - timedelta(days=5)),
            (True, 'Linux', 'en-US', 'orange', now - timedelta(days=4)),
            (True, 'Linux', 'en-US', 'apple', now - timedelta(days=3)),
            (False, 'Windows XP', 'en-US', 'banana', now - timedelta(days=2)),
            (False, 'Windows 7', 'en-US', 'orange', now - timedelta(days=1)),
            (False, 'Linux', 'es', 'apple', now - timedelta(days=0)),
        ]
        for happy, platform, locale, description, created in items:
            # We don't need to keep this around, just need to create it.
            simple(happy=happy, platform=platform, locale=locale,
                   description=description, created=created, save=True)

        self.refresh()

    def test_front_page(self):
        url = reverse('dashboard')
        r = self.client.get(url)
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'analytics/dashboard.html')

        pq = PyQuery(r.content)
        # Make sure that each opinion is show, and that the count is correct.
        eq_(pq('.block.count strong').text(), '7')
        eq_(len(pq('li.opinion')), 7)

    def test_search(self):
        url = reverse('dashboard')
        # Happy
        r = self.client.get(url, {'happy': 1})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 4)
        # Sad
        r = self.client.get(url, {'happy': 0})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 3)
        # Locale
        r = self.client.get(url, {'locale': 'es'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 2)
        # Platform and happy
        r = self.client.get(url, {'happy': 1, 'platform': 'Linux'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 2)
        # Empty search
        r = self.client.get(url, {'platform': 'Atari'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

    def test_text_search(self):
        url = reverse('dashboard')
        # Text search
        r = self.client.get(url, {'q': 'apple'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 3)
        # Text and filter
        r = self.client.get(url, {'q': 'apple', 'happy': 1, 'locale': 'en-US'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 2)

    def test_date_search(self):
        url = reverse('dashboard')
        # These start and end dates will give known slices of the data.
        # Silly relative dates.
        start = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        end = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),

        # Unspecified start => (-infin, end]
        r = self.client.get(url, {
                'date_end': end,
            })
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 5)

        # Unspecified end => [start, +infin)
        r = self.client.get(url, {
                'date_start': start
            })
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 6)

        # Both start and end => [start, end]
        r = self.client.get(url, {
                'date_start': start,
                'date_end': end,
            })
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 4)

    def test_invalid_search(self):
        url = reverse('dashboard')
        # Invalid values for happy shouldn't filter
        r = self.client.get(url, {'happy': 'fish'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)
        # Unknown parameters should be ignored.
        r = self.client.get(url, {'apples': 'oranges'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)
        # An empty query string shouldn't be treated like a search.
        r = self.client.get(url, {'platform': ''})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)
        # A broken date range search shouldn't affect anything
        # Why this? Because this is the thing the fuzzer found.
        r = self.client.get(url, {
                'date_end': '/etc/shadow\x00',
                'date_start': '/etc/passwd\x00'
                })
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

    def test_frontpage_index_missing(self):
        """If index is missing, show es_down template."""
        self.teardown_indexes()
        resp = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(resp, 'analytics/es_down.html')

    def test_zero_fill(self):
        """If a day in a date range has no data, it should be zero filled."""
        # Note that we request a date range that includes 3 days without data.
        url = reverse('dashboard')
        start = (datetime.now() - timedelta(days=9))
        end = (datetime.now() - timedelta(days=3))

        r = self.client.get(url, {
                'date_start': start.strftime('%Y-%m-%d'),
                'date_end': end.strftime('%Y-%m-%d'),
            })
        # The histogram data is of the form [d, v], where d is a number of
        # milliseconds since the epoch, and v is the value at that time stamp.
        dates = [d[0] for d in r.context['histogram'][0]['data']]
        dates = [datetime.fromtimestamp(d / 1000) for d in dates]
        days = [d.day for d in dates]

        d = start
        while d <= end:
            assert d.day in days, "Day %s has no data." % d.day
            d += timedelta(days=1)

    def test_frontpage_es_down(self):
        """If can't connect to ES, show es_down template."""
        # TODO: Rewrite this with Mock.
        old_counts_to_options = views.counts_to_options
        try:
            def mock_counts_to_options(*args, **kwargs):
                raise Timeout()
            views.counts_to_options = mock_counts_to_options

            resp = self.client.get(reverse('dashboard'))
            self.assertTemplateUsed(resp, 'analytics/es_down.html')

        finally:
            views.counts_to_options = old_counts_to_options
