from datetime import date, datetime, timedelta

from pyquery import PyQuery

from fjord.base.tests import (
    AnalyzerProfileFactory,
    LocalizingClient,
    reverse,
    TestCase
)
from fjord.feedback.tests import (
    ProductFactory,
    ResponseFactory,
    ResponseEmailFactory
)
from fjord.search.tests import ElasticTestCase


class TestAnalyticsDashboardView(ElasticTestCase):
    client_class = LocalizingClient

    def test_permissions(self):
        # Verifies that only analyzers can see the analytics dashboard
        # link
        resp = self.client.get(reverse('dashboard'))
        assert 200 == resp.status_code
        assert 'adashboard' not in resp.content

        # Verifies that only analyzers can see the analytics dashboard
        resp = self.client.get(reverse('analytics_dashboard'))
        assert 403 == resp.status_code

        # Verify analyzers can see analytics dashboard link
        jane = AnalyzerProfileFactory(user__email='jane@example.com').user

        self.client_login_user(jane)

        resp = self.client.get(reverse('dashboard'))
        assert 200 == resp.status_code
        assert 'adashboard' in resp.content

        # Verify analyzers can see analytics dashboard
        resp = self.client.get(reverse('analytics_dashboard'))
        assert 200 == resp.status_code


class TestSearchView(ElasticTestCase):
    client_class = LocalizingClient
    url = reverse('analytics_search')

    # Note: We count the number of td.sentiment things since there's
    # one sentiment-classed td element for every feedback response
    # that shows up in the search results.

    def setUp(self):
        super(TestSearchView, self).setUp()
        # Set up some sample data
        # 4 happy, 3 sad.
        # 2 Windows XP, 2 Linux, 1 OS X, 2 Windows 7
        now = datetime.now()
        # The dashboard by default shows the last week of data, so
        # these need to be relative to today. The alternative is that
        # every test gives an explicit date range, and that is
        # annoying and verbose.
        items = [
            # happy, platform, locale, description, created
            (True, '', 'en-US', 'apple', now - timedelta(days=6)),
            (True, 'Windows 7', 'es', 'banana', now - timedelta(days=5)),
            (True, 'Linux', 'en-US', 'orange', now - timedelta(days=4)),
            (True, 'Linux', 'en-US', 'apple', now - timedelta(days=3)),
            (False, 'Windows XP', 'en-US', 'banana', now - timedelta(days=2)),
            (False, 'Windows 7', 'en-US', 'orange', now - timedelta(days=1)),
            (False, 'Linux', 'es', u'\u2713 apple', now),
        ]
        for happy, platform, locale, description, created in items:
            # We don't need to keep this around, just need to create it.
            ResponseFactory(happy=happy, platform=platform, locale=locale,
                            description=description, created=created)

        self.refresh()

        # Create analyzer and log analyzer in
        jane = AnalyzerProfileFactory(user__email='jane@example.com').user

        self.client_login_user(jane)

    def test_zero_fill(self):
        """If a day in a date range has no data, it should be zero filled."""
        # Note that we request a date range that includes 3 days without data.
        start = (date.today() - timedelta(days=9))
        end = (date.today() - timedelta(days=3))

        r = self.client.get(self.url, {
            'date_start': start.strftime('%Y-%m-%d'),
            'date_end': end.strftime('%Y-%m-%d'),
        })
        # The histogram data is of the form [d, v], where d is a number of
        # milliseconds since the epoch, and v is the value at that time stamp.
        dates = [d[0] for d in r.context['histogram'][0]['data']]
        dates = [date.fromtimestamp(d // 1000) for d in dates]
        days = [d.day for d in dates]

        d = start
        # FIXME: This seems like it should be <= end (including the
        # end date), but what happens is that that includes an extra
        # day. I suspect there's some funny business in regards to
        # timezones and we're actually looking at a late time for the
        # previous day for each day because of timezones and then that
        # gets handled in flot after being converted to UTC or
        # something like that.  The point being that "end" is actually
        # not the end point we want to test against.
        while d < end:
            assert d.day in days, 'Day %s has no data.' % d.day
            d += timedelta(days=1)

    def test_front_page(self):
        r = self.client.get(self.url)
        assert 200 == r.status_code
        self.assertTemplateUsed(r, 'analytics/analyzer/search.html')

        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 7

    def test_search(self):
        # Happy
        r = self.client.get(self.url, {'happy': 1})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 4

        # Sad
        r = self.client.get(self.url, {'happy': 0})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 3

        # Locale
        r = self.client.get(self.url, {'locale': 'es'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 2

        # Platform and happy
        r = self.client.get(self.url, {'happy': 1, 'platform': 'Linux'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 2

        # Product
        r = self.client.get(self.url, {'product': 'Firefox'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 7

        # Product
        r = self.client.get(self.url, {'product': 'Firefox for Android'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 0

        # Product version
        r = self.client.get(
            self.url, {'product': 'Firefox', 'version': '17.0'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 7

        # Product version
        r = self.client.get(
            self.url, {'product': 'Firefox', 'version': '18.0'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 0

        # Empty search
        r = self.client.get(self.url, {'platform': 'Atari'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 0

    def test_has_email(self):
        # Test before we create a responsemail
        r = self.client.get(self.url, {'has_email': '0'})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 7

        r = self.client.get(self.url, {'has_email': '1'})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 0

        ResponseEmailFactory(
            opinion__happy=True,
            opinion__product=u'Firefox',
            opinion__description=u'ou812',
            opinion__created=datetime.now())

        # Have to reindex everything because unlike in a request
        # context, what happens here is we index the Response, but
        # without the ResponseEmail.
        self.setup_indexes()

        r = self.client.get(self.url, {'has_email': '0'})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert 'ou812' not in r.content
        assert len(pq('li.opinion')) == 7

        r = self.client.get(self.url, {'has_email': '1'})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert 'ou812' in r.content
        assert len(pq('li.opinion')) == 1

    def test_country(self):
        ResponseEmailFactory(
            opinion__happy=True,
            opinion__product=u'Firefox OS',
            opinion__description=u'ou812',
            opinion__country=u'ES',
            opinion__created=datetime.now())
        # Have to reindex everything because unlike in a request
        # context, what happens here is we index the Response, but
        # without the ResponseEmail.
        self.setup_indexes()

        r = self.client.get(self.url, {
            'product': 'Firefox OS', 'country': 'ES'})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert 'ou812' in r.content
        assert len(pq('li.opinion')) == 1

    def test_empty_and_unknown(self):
        # Empty value should work
        r = self.client.get(self.url, {'platform': ''})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 1

        # "Unknown" value should also work
        r = self.client.get(self.url, {'platform': 'Unknown'})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 1

    def test_version_noop(self):
        """version has no effect if product isn't set"""
        # Filter on product and version--both filters affect the
        # results
        r = self.client.get(
            self.url, {'product': 'Firefox', 'version': '18.0'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 0

        # Filter on version--filter has no effect on results
        r = self.client.get(
            self.url, {'version': '18.0'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 7

    def test_text_search(self):
        # Text search
        r = self.client.get(self.url, {'q': 'apple'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 3

        # Text and filter
        r = self.client.get(
            self.url, {'q': 'apple', 'happy': 1, 'locale': 'en-US'})
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 2

    def test_text_search_unicode(self):
        """Unicode in the search field shouldn't kick up errors"""
        # Text search
        r = self.client.get(self.url, {'q': u'\u2713'})
        assert r.status_code == 200

    def test_date_search(self):
        # These start and end dates will give known slices of the data.
        # Silly relative dates.
        start = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        end = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),

        # Unspecified start => (-infin, end]
        r = self.client.get(self.url, {
            'date_end': end,
        })
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 5

        # Unspecified end => [start, +infin)
        r = self.client.get(self.url, {
            'date_start': start
        })
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 6

        # Both start and end => [start, end]
        r = self.client.get(self.url, {
            'date_start': start,
            'date_end': end,
        })
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 4

    def test_date_start_valueerror(self):
        # https://bugzilla.mozilla.org/show_bug.cgi?id=898584
        r = self.client.get(self.url, {
            'date_start': '0001-01-01',
        })
        assert r.status_code == 200

    def test_invalid_search(self):
        # Invalid values for happy shouldn't filter
        r = self.client.get(self.url, {'happy': 'fish'})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 7

        # Unknown parameters should be ignored.
        r = self.client.get(self.url, {'apples': 'oranges'})
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 7

        # A broken date range search shouldn't affect anything
        # Why this? Because this is the thing the fuzzer found.
        r = self.client.get(self.url, {
            'date_end': '/etc/shadow\x00',
            'date_start': '/etc/passwd\x00'
        })
        assert r.status_code == 200
        pq = PyQuery(r.content)
        assert len(pq('li.opinion')) == 7

    def test_search_export_csv(self):
        r = self.client.get(self.url, {'format': 'csv'})
        assert r.status_code == 200

        # Check that it parses in csv with n rows.
        lines = r.content.splitlines()

        # URL row, params row, header row and one row for every opinion
        assert len(lines) == 10


class ProductsTestCase(TestCase):
    client_class = LocalizingClient

    def test_permissions_and_basic_view(self):
        prod = ProductFactory(display_name='Rehan')
        resp = self.client.get(reverse('analytics_products'))
        assert resp.status_code == 403

        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        resp = self.client.get(reverse('analytics_products'))
        assert resp.status_code == 200
        assert prod.display_name in resp.content

    def test_add_product(self):
        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        data = {
            'enabled': True,
            'display_name': 'Rehan',
            'display_description': '*the* Rehan',
            'db_name': 'rehan',
            'slug': 'rehan',
            'on_dashboard': True,
            'on_picker': True,
            'browser': '',
            'browser_data_browser': '',
            'notes': ''
        }

        resp = self.client.post(
            reverse('analytics_products'), data, follow=True
        )
        assert resp.status_code == 200
        assert data['display_name'] in resp.content

    def test_update_product(self):
        prod = ProductFactory(display_name='Rehan')

        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        data = {
            'id': prod.id,
            'enabled': prod.enabled,
            'display_name': 'Rehan v2',
            'display_description': prod.display_description,
            'db_name': prod.db_name,
            'slug': prod.slug,
            'on_dashboard': prod.on_dashboard,
            'on_picker': prod.on_picker,
            'borwser': '',
            'browser_data_browser': '',
            'notes': ''
        }

        resp = self.client.post(
            reverse('analytics_products'), data, follow=True
        )
        assert resp.status_code == 200
        assert data['display_name'] in resp.content
