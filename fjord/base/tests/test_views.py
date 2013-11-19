from django.test.utils import override_settings

from nose.tools import eq_

from fjord.base import views
from fjord.base.tests import LocalizingClient, reverse, TestCase
from fjord.base.views import IntentionalException
from fjord.search.tests import ElasticTestCase


class TestAbout(TestCase):
    client_class = LocalizingClient

    def test_about_view(self):
        r = self.client.get(reverse('about-view'))
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'about.html')

        r = self.client.get(reverse('about-view'), {'mobile': 1})
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'mobile/about.html')


class TestLoginFailure(TestCase):
    def test_login_failure_view(self):
        r = self.client.get(reverse('login-failure'))
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'login_failure.html')

        r = self.client.get(reverse('login-failure'), {'mobile': 1})
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'mobile/login_failure.html')


# Note: This needs to be an ElasticTestCase because the view does ES
# stuff.
class MonitorViewTest(ElasticTestCase):
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
                        'BACKEND': 'caching.backends.memcached.CacheClass',
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

                eq_(resp.status_code, 200, '%s != %s (%s)' % (
                        resp.status_code, 200, repr(errors)))

        finally:
            views.test_memcached = test_memcached

    @override_settings(SHOW_STAGE_NOTICE=True)
    def test_500(self):
        with self.assertRaises(IntentionalException) as cm:
            self.client.get('/services/throw-error')

        eq_(type(cm.exception), IntentionalException)


class ErrorTesting(ElasticTestCase):
    client_class = LocalizingClient

    def test_404(self):
        request = self.client.get('/a/path/that/should/never/exist')
        eq_(request.status_code, 404)
        self.assertTemplateUsed(request, '404.html')


class TestRobots(TestCase):
    def test_robots(self):
        resp = self.client.get('/robots.txt')
        eq_(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'robots.txt')


class TestNewUserView(TestCase):
    def test_redirect_to_dashboard_if_anonymous(self):
        # AnonymousUser shouldn't get to the new-user-view, so make
        # sure they get redirected to the dashboard.
        resp = self.client.get(reverse('new-user-view'), follow=True)
        print resp.content
        print resp.status_code
        eq_(resp.status_code, 200)
        self.assertTemplateNotUsed('new_user.html')
        self.assertTemplateUsed('analytics/dashboard.html')
