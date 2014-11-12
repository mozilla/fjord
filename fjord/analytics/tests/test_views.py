import json
import logging
from datetime import date, datetime, timedelta

from elasticsearch.exceptions import ConnectionError
from nose.tools import eq_
from pyquery import PyQuery

from django.contrib.auth.models import Group
from django.http import QueryDict

from fjord.analytics import views
from fjord.base.tests import LocalizingClient, ProfileFactory, reverse
from fjord.feedback.tests import ResponseFactory, ProductFactory
from fjord.search.tests import ElasticTestCase


logger = logging.getLogger(__name__)


class TestDashboardView(ElasticTestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(TestDashboardView, self).setUp()
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

    def test_front_page(self):
        url = reverse('dashboard')
        r = self.client.get(url)
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'analytics/dashboard.html')

        pq = PyQuery(r.content)
        # Make sure that each opinion is shown and that the count is correct.
        eq_(pq('.block.count strong').text(), '7')
        eq_(len(pq('li.opinion')), 7)

    def test_hidden_products_dont_show_up(self):
        # Create a hidden product and one response for it
        prod = ProductFactory(
            display_name=u'HiddenProduct', db_name='HiddenProduct',
            on_dashboard=False)
        ResponseFactory(product=prod.db_name)
        self.refresh()

        url = reverse('dashboard')
        resp = self.client.get(url)
        eq_(resp.status_code, 200)

        assert 'HiddenProduct' not in resp.content

    def test_cant_see_old_responses(self):
        # Make sure we can't see responses from > 180 days ago
        cutoff = datetime.today() - timedelta(days=180)
        ResponseFactory(description='Young enough--Party!',
                        created=cutoff + timedelta(days=1))
        ResponseFactory(description='Too old--Get off my lawn!',
                        created=cutoff - timedelta(days=1))
        self.refresh()

        url = reverse('dashboard')
        resp = self.client.get(url, {
            'date_start': cutoff.strftime('%Y-%m-%d')}
        )
        assert 'Young enough--Party!' in resp.content
        assert 'Too old--Get off my lawn!' not in resp.content

    def test_dashboard_atom_links(self):
        """Test dashboard atom links are correct"""
        r = self.client.get(reverse('dashboard'))
        eq_(200, r.status_code)
        assert '/en-US/?format=atom' in r.content

        r = self.client.get(
            reverse('dashboard'),
            {'happy': 1})
        eq_(200, r.status_code)
        pq = PyQuery(r.content)
        pq = pq('link[type="application/atom+xml"]')
        qs = QueryDict(pq[0].attrib['href'].split('?')[1])
        eq_(qs['happy'], u'1')
        eq_(qs['format'], u'atom')

        r = self.client.get(
            reverse('dashboard'),
            {'product': 'Firefox', 'version': '20.0'})
        eq_(200, r.status_code)
        pq = PyQuery(r.content)
        pq = pq('link[type="application/atom+xml"]')
        qs = QueryDict(pq[0].attrib['href'].split('?')[1])
        eq_(qs['product'], u'Firefox')
        eq_(qs['version'], u'20.0')

    def test_truncated_description_on_dashboard(self):
        # Create a description that's 500 characters long (which is
        # the truncation length) plus a string that's easy to assert
        # non-existence of.
        desc = ('0' * 500) + 'OMGou812'
        ResponseFactory(description=desc)
        self.refresh()

        url = reverse('dashboard')
        r = self.client.get(url)
        assert 'OMGou812' not in r.content

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

        # Product
        r = self.client.get(url, {'product': 'Firefox'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

        # Product
        r = self.client.get(url, {'product': 'Firefox for Android'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

        # Product version
        r = self.client.get(
            url, {'product': 'Firefox', 'version': '17.0'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

        # Product version
        r = self.client.get(
            url, {'product': 'Firefox', 'version': '18.0'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

        # Empty search
        r = self.client.get(url, {'platform': 'Atari'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

    def test_empty_and_unknown(self):
        url = reverse('dashboard')

        # Empty value should work
        r = self.client.get(url, {'platform': ''})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 1)

        # "Unknown" value should also work
        r = self.client.get(url, {'platform': 'Unknown'})
        eq_(r.status_code, 200)
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 1)

    def test_version_noop(self):
        """version has no effect if product isn't set"""
        url = reverse('dashboard')

        # Filter on product and version--both filters affect the
        # results
        r = self.client.get(
            url, {'product': 'Firefox', 'version': '18.0'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 0)

        # Filter on version--filter has no effect on results
        r = self.client.get(
            url, {'version': '18.0'})
        pq = PyQuery(r.content)
        eq_(len(pq('li.opinion')), 7)

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

    def test_text_search_unicode(self):
        """Unicode in the search field shouldn't kick up errors"""
        url = reverse('dashboard')
        # Text search
        r = self.client.get(url, {'q': u'\u2713'})
        eq_(r.status_code, 200)

    def test_search_format_json(self):
        """JSON output works"""
        url = reverse('dashboard')
        # Text search
        r = self.client.get(url, {'q': u'apple', 'format': 'json'})
        eq_(r.status_code, 200)

        content = json.loads(r.content)
        eq_(content['total'], 3)
        eq_(len(content['results']), 3)

    def test_search_format_atom(self):
        """Atom output works"""
        url = reverse('dashboard')
        # Text search
        r = self.client.get(url, {'q': u'apple', 'format': 'atom'})
        eq_(r.status_code, 200)

        assert 'http://www.w3.org/2005/Atom' in r.content

    # FIXME - This was backed out. We can re-enable this test when urls are
    # re-added.
    # def test_search_format_atom_has_related_links(self):
    #     """Atom output works"""
    #     response(description='relatedlinks', url='http://example.com',
    #              save=True)
    #     self.refresh()

    #     url = reverse('dashboard')
    #     # Text search
    #     r = self.client.get(url, {'q': 'relatedlinks', 'format': 'atom'})
    #     eq_(r.status_code, 200)

    #     assert 'http://www.w3.org/2005/Atom' in r.content
    #     # FIXME: This is a lousy way to test for a single link with
    #     # both attributes.
    #     assert 'rel="related"' in r.content
    #     assert 'href="http://example.com"' in r.content

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

    def test_date_start_valueerror(self):
        # https://bugzilla.mozilla.org/show_bug.cgi?id=898584
        url = reverse('dashboard')
        r = self.client.get(url, {
            'date_start': '0001-01-01',
        })
        eq_(r.status_code, 200)

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
        start = (date.today() - timedelta(days=9))
        end = (date.today() - timedelta(days=3))

        r = self.client.get(url, {
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
            assert d.day in days, "Day %s has no data." % d.day
            d += timedelta(days=1)

    def test_frontpage_es_down(self):
        """If can't connect to ES, show es_down template."""
        # TODO: Rewrite this with Mock.
        old_counts_to_options = views.counts_to_options
        try:
            def mock_counts_to_options(*args, **kwargs):
                raise ConnectionError()
            views.counts_to_options = mock_counts_to_options

            resp = self.client.get(reverse('dashboard'))
            self.assertTemplateUsed(resp, 'analytics/es_down.html')

        finally:
            views.counts_to_options = old_counts_to_options


class TestResponseview(ElasticTestCase):
    client_class = LocalizingClient

    def test_response_view(self):
        """Test dashboard link goes to response view"""
        resp = ResponseFactory(happy=True, description=u'the best!')

        self.refresh()

        url = reverse('dashboard')
        r = self.client.get(url)
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'analytics/dashboard.html')

        pq = PyQuery(r.content)
        # Get the permalink
        permalink = pq('li.opinion a[href*="response"]').attr('href')

        r = self.client.get(permalink)
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'analytics/response.html')
        assert str(resp.description) in r.content

    def test_response_view_mobile(self):
        """Test response mobile view doesn't die"""
        resp = ResponseFactory(happy=True, description=u'the best!')

        self.refresh()

        r = self.client.get(reverse('response_view', args=(resp.id,)),
                            {'mobile': 1})
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'analytics/mobile/response.html')
        assert str(resp.description) in r.content

    def test_response_view_analyzer(self):
        """Test secret section only shows up for analyzers"""
        resp = ResponseFactory(happy=True, description=u'the bestest best!')

        self.refresh()
        r = self.client.get(reverse('response_view', args=(resp.id,)))

        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'analytics/response.html')
        assert str(resp.description) in r.content

        # Verify there is no secret area visible for non-analyzers.
        pq = PyQuery(r.content)
        secretarea = pq('dl.secret')
        eq_(len(secretarea), 0)

        jane = ProfileFactory(user__email='jane@example.com').user
        jane.groups.add(Group.objects.get(name='analyzers'))

        self.client_login_user(jane)
        r = self.client.get(reverse('response_view', args=(resp.id,)))

        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'analytics/response.html')
        assert str(resp.description) in r.content

        # Verify the secret area is there.
        pq = PyQuery(r.content)
        secretarea = pq('dl.secret')
        eq_(len(secretarea), 1)

        # Verify there is an mlt section in the secret area.
        mlt = pq('dd#mlt')
        eq_(len(mlt), 1)
