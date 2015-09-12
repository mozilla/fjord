import json

from django.test.utils import override_settings

import pytest
from pyquery import PyQuery

from fjord.base import views
from fjord.base.tests import (
    LocalizingClient,
    TestCase,
    AnalyzerProfileFactory,
    reverse
)
from fjord.base.views import IntentionalException
from fjord.search.tests import ElasticTestCase


class TestAbout(TestCase):
    client_class = LocalizingClient

    def test_about_view(self):
        resp = self.client.get(reverse('about-view'))
        assert resp.status_code == 200
        self.assertTemplateUsed(resp, 'about.html')


class TestLoginFailure(TestCase):
    def test_login_failure_view(self):
        resp = self.client.get(reverse('login-failure'))
        assert resp.status_code == 200
        self.assertTemplateUsed(resp, 'login_failure.html')

        resp = self.client.get(reverse('login-failure'), {'mobile': 1})
        assert resp.status_code == 200
        self.assertTemplateUsed(resp, 'mobile/login_failure.html')


# Note: This needs to be an ElasticTestCase because the view does ES
# stuff.
class TestMonitorView(ElasticTestCase):
    def test_monitor_view(self):
        """Tests for the monitor view."""
        # TODO: When we add a mocking framework, we can mock this
        # properly.
        test_memcached = views.test_memcached
        try:
            with self.settings(
                SHOW_STAGE_NOTICE=True,
                CACHES={
                    'default': {
                        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',  # noqa
                        'LOCATION': ['localhost:11211', 'localhost2:11211']
                    }
                }):

                # Mock the test_memcached function so it always returns
                # True.
                views.test_memcached = lambda host, port: True

                # TODO: Replace when we get a mock library.
                def mock_rabbitmq():
                    class MockRabbitMQ(object):
                        def connect(self):
                            return True
                    return lambda *a, **kw: MockRabbitMQ()
                views.establish_connection = mock_rabbitmq()

                # Request /services/monitor and make sure it returns
                # HTTP 200 and that there aren't errors on the page.
                resp = self.client.get(reverse('services-monitor'))
                errors = [line for line in resp.content.splitlines()
                          if 'ERROR' in line]

                assert resp.status_code == 200, '%s != %s (%s)' % (
                    resp.status_code, 200, repr(errors))

        finally:
            views.test_memcached = test_memcached


class TestFileNotFound(TestCase):
    client_class = LocalizingClient

    def test_404(self):
        request = self.client.get('/a/path/that/should/never/exist')
        assert request.status_code == 404
        self.assertTemplateUsed(request, '404.html')


class TestServerError(TestCase):
    @override_settings(SHOW_STAGE_NOTICE=True)
    def test_500(self):
        with pytest.raises(IntentionalException):
            self.client.get('/services/throw-error')


class TestRobots(TestCase):
    def test_robots(self):
        resp = self.client.get('/robots.txt')
        assert resp.status_code == 200
        self.assertTemplateUsed(resp, 'robots.txt')


class TestContribute(TestCase):
    def test_contribute(self):
        resp = self.client.get('/contribute.json')
        assert resp.status_code == 200
        self.assertTemplateUsed(resp, 'contribute.json')

    def test_contribute_if_valid_json(self):
        resp = self.client.get('/contribute.json')
        # json.loads throws a ValueError when contribute.json is invalid JSON.
        json.loads(resp.content)


class TestNewUserView(ElasticTestCase):
    def setUp(self):
        super(TestNewUserView, self).setUp()
        jane = AnalyzerProfileFactory().user
        self.jane = jane

    def test_redirect_to_dashboard_if_anonymous(self):
        # AnonymousUser shouldn't get to the new-user-view, so make
        # sure they get redirected to the dashboard.
        resp = self.client.get(reverse('new-user-view'), follow=True)
        assert resp.status_code == 200
        self.assertTemplateNotUsed('new_user.html')
        self.assertTemplateUsed('analytics/dashboard.html')

    def test_default_next_url(self):
        self.client_login_user(self.jane)
        resp = self.client.get(reverse('new-user-view'))
        assert resp.status_code == 200
        self.assertTemplateUsed('new_user.html')

        # Pull out next link
        pq = PyQuery(resp.content)
        next_url = pq('#next-url-link')
        assert next_url.attr['href'] == '/en-US/'  # this is the dashboard

    def test_valid_next_url(self):
        self.client_login_user(self.jane)
        url = reverse('new-user-view')
        resp = self.client.get(url, {
            'next': '/ou812'  # stretches the meaning of 'valid'
        })
        assert resp.status_code == 200
        self.assertTemplateUsed('new_user.html')

        # Pull out next link which is naughty, so it should have been
        # replaced with a dashboard link.
        pq = PyQuery(resp.content)
        next_url = pq('#next-url-link')
        assert next_url.attr['href'] == '/ou812'

    def test_sanitized_next_url(self):
        self.client_login_user(self.jane)
        url = reverse('new-user-view')
        resp = self.client.get(url, {
            'next': 'javascript:prompt%28document.cookie%29'
        })
        assert resp.status_code == 200
        self.assertTemplateUsed('new_user.html')

        # Pull out next link which is naughty, so it should have been
        # replaced with a dashboard link.
        pq = PyQuery(resp.content)
        next_url = pq('#next-url-link')
        assert next_url.attr['href'] == '/en-US/'  # this is the dashboard
