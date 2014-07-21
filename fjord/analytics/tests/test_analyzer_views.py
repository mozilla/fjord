import logging
from datetime import datetime, timedelta

from nose.tools import eq_, ok_
from pyquery import PyQuery

from django.contrib.auth.models import Group

from fjord.base.tests import LocalizingClient, ProfileFactory, reverse
from fjord.feedback.tests import ResponseFactory, ResponseEmailFactory
from fjord.search.tests import ElasticTestCase


logger = logging.getLogger(__name__)


class TestAnalyticsDashboardView(ElasticTestCase):
    client_class = LocalizingClient

    def test_permissions(self):
        # Verifies that only analyzers can see the analytics dashboard
        # link
        resp = self.client.get(reverse('dashboard'))
        eq_(200, resp.status_code)
        assert 'adashboard' not in resp.content

        # Verifies that only analyzers can see the analytics dashboard
        resp = self.client.get(reverse('analytics_dashboard'))
        eq_(403, resp.status_code)

        # Verify analyzers can see analytics dashboard link
        jane = ProfileFactory(user__email='jane@example.com').user
        jane.groups.add(Group.objects.get(name='analyzers'))

        self.client_login_user(jane)

        resp = self.client.get(reverse('dashboard'))
        eq_(200, resp.status_code)
        assert 'adashboard' in resp.content

        # Verify analyzers can see analytics dashboard
        resp = self.client.get(reverse('analytics_dashboard'))
        eq_(200, resp.status_code)


class TestOccurrencesView(ElasticTestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(TestOccurrencesView, self).setUp()
        # Set up some sample data
        items = [
            # happy, locale, description
            (True, 'en-US', 'apple banana orange pear'),
            (True, 'en-US', 'orange pear kiwi'),
            (True, 'en-US', 'chocolate chocolate yum'),
            (False, 'en-US', 'apple banana grapefruit'),

            # This one doesn't create bigrams because there isn't enough words
            (False, 'en-US', 'orange'),

            # This one shouldn't show up
            (False, 'es', 'apple banana'),
        ]
        for happy, locale, description in items:
            ResponseFactory(happy=happy, locale=locale,
                            description=description)

        self.refresh()

        # Create analyzer and log analyzer in
        jane = ProfileFactory(user__email='jane@example.com').user
        jane.groups.add(Group.objects.get(name='analyzers'))

        self.client_login_user(jane)

    def test_occurrences(self):
        url = reverse('analytics_occurrences')

        # No results when you initially look at the page
        resp = self.client.get(url)
        eq_(200, resp.status_code)
        assert 'id="results"' not in resp.content

        # 'product' is a required field
        resp = self.client.get(url, {'product': ''})
        eq_(200, resp.status_code)
        # FIXME - this test is too loose
        assert 'This field is required' in resp.content

        # At least a version, search term or start date is required
        resp = self.client.get(url, {'product': 'Firefox'})
        eq_(200, resp.status_code)
        assert 'This field is required' not in resp.content
        assert 'Must specify at least one' in resp.content

        # Minimal required for results
        resp = self.client.get(url, {
            'product': 'Firefox',
            'first_version': '17.0'}
        )
        eq_(200, resp.status_code)
        assert 'This field is required' not in resp.content
        assert 'Must speicfy at least one' not in resp.content
        assert 'id="results"' in resp.content

        # FIXME - when things are less prototypy, add tests for
        # specific results


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
            (False, 'Linux', 'es', u'\u2713 apple', now - timedelta(days=0)),
        ]
        for happy, platform, locale, description, created in items:
            # We don't need to keep this around, just need to create it.
            ResponseFactory(happy=happy, platform=platform, locale=locale,
                            description=description, created=created)

        self.refresh()

        # Create analyzer and log analyzer in
        jane = ProfileFactory(user__email='jane@example.com').user
        jane.groups.add(Group.objects.get(name='analyzers'))

        self.client_login_user(jane)

    def test_front_page(self):
        r = self.client.get(self.url)
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'analytics/analyzer/search.html')

        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

    def test_search(self):
        # Happy
        r = self.client.get(self.url, {'happy': 1})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 4)

        # Sad
        r = self.client.get(self.url, {'happy': 0})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 3)

        # Locale
        r = self.client.get(self.url, {'locale': 'es'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 2)

        # Platform and happy
        r = self.client.get(self.url, {'happy': 1, 'platform': 'Linux'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 2)

        # Product
        r = self.client.get(self.url, {'product': 'Firefox'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

        # Product
        r = self.client.get(self.url, {'product': 'Firefox for Android'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

        # Product version
        r = self.client.get(
            self.url, {'product': 'Firefox', 'version': '17.0'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

        # Product version
        r = self.client.get(
            self.url, {'product': 'Firefox', 'version': '18.0'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

        # Empty search
        r = self.client.get(self.url, {'platform': 'Atari'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

    def test_has_email(self):
        # Test before we create a responsemail
        r = self.client.get(self.url, {'has_email': '0'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

        r = self.client.get(self.url, {'has_email': '1'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

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
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        ok_('ou812' not in r.content)
        eq_(len(pq('li.opinion')), 7)

        r = self.client.get(self.url, {'has_email': '1'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        ok_('ou812' in r.content)
        eq_(len(pq('li.opinion')), 1)

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
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        ok_('ou812' in r.content)
        eq_(len(pq('li.opinion')), 1)

    def test_empty_and_unknown(self):
        # Empty value should work
        r = self.client.get(self.url, {'platform': ''})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 1)

        # "Unknown" value should also work
        r = self.client.get(self.url, {'platform': 'Unknown'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 1)

    def test_version_noop(self):
        """version has no effect if product isn't set"""
        # Filter on product and version--both filters affect the
        # results
        r = self.client.get(
            self.url, {'product': 'Firefox', 'version': '18.0'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

        # Filter on version--filter has no effect on results
        r = self.client.get(
            self.url, {'version': '18.0'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

    def test_text_search(self):
        # Text search
        r = self.client.get(self.url, {'q': 'apple'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 3)

        # Text and filter
        r = self.client.get(
            self.url, {'q': 'apple', 'happy': 1, 'locale': 'en-US'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 2)

    def test_text_search_unicode(self):
        """Unicode in the search field shouldn't kick up errors"""
        # Text search
        r = self.client.get(self.url, {'q': u'\u2713'})
        eq_(r.status_code, 200)

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
        eq_(len(pq('li.opinion')), 5)

        # Unspecified end => [start, +infin)
        r = self.client.get(self.url, {
                'date_start': start
            })
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 6)

        # Both start and end => [start, end]
        r = self.client.get(self.url, {
                'date_start': start,
                'date_end': end,
            })
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 4)

    def test_date_start_valueerror(self):
        # https://bugzilla.mozilla.org/show_bug.cgi?id=898584
        r = self.client.get(self.url, {
                'date_start': '0001-01-01',
            })
        eq_(r.status_code, 200)

    def test_invalid_search(self):
        # Invalid values for happy shouldn't filter
        r = self.client.get(self.url, {'happy': 'fish'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

        # Unknown parameters should be ignored.
        r = self.client.get(self.url, {'apples': 'oranges'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

        # A broken date range search shouldn't affect anything
        # Why this? Because this is the thing the fuzzer found.
        r = self.client.get(self.url, {
                'date_end': '/etc/shadow\x00',
                'date_start': '/etc/passwd\x00'
                })
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

    def test_search_export_csv(self):
        r = self.client.get(self.url, {'format': 'csv'})
        eq_(r.status_code, 200)

        # Check that it parses in csv with n rows.
        lines = r.content.splitlines()

        # URL row, params row, header row and one row for every opinion
        eq_(len(lines), 10)
