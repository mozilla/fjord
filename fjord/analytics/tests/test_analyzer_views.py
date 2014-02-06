import json
import logging

from nose.tools import eq_
from pyelasticsearch.exceptions import Timeout
from pyquery import PyQuery

from django.contrib.auth.models import Group
from django.http import QueryDict

from fjord.analytics import views
from fjord.analytics.tools import counts_to_options, zero_fill
from fjord.base.tests import TestCase, LocalizingClient, profile, reverse, user
from fjord.base.util import epoch_milliseconds
from fjord.feedback.tests import response
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
        jane = user(email='jane@example.com', save=True)
        profile(user=jane, save=True)
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
            response(
                happy=happy, locale=locale, description=description, save=True)

        self.refresh()

        # Create analyzer and log analyzer in
        jane = user(email='jane@example.com', save=True)
        profile(user=jane, save=True)
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
            'first_version': '17.0.0'}
        )
        eq_(200, resp.status_code)
        assert 'This field is required' not in resp.content
        assert 'Must speicfy at least one' not in resp.content
        assert 'id="results"' in resp.content

        # FIXME - when things are less prototypy, add tests for
        # specific results
