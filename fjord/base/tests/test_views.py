from nose.tools import eq_

from fjord.base import views
from fjord.base.tests import LocalizingClient, reverse
from fjord.search.tests import ElasticTestCase


# Note: This needs to be an ElasticTestCase because the view does ES
# stuff.
class MonitorViewTest(ElasticTestCase):
    client_class = LocalizingClient

    def test_monitor_view(self):
        """Tests for the monitor view."""
        # TODO: When we add a mocking framework, we can mock this
        # properly.
        test_memcached = views.test_memcached
        try:
            with self.settings(
                # Note: tower dies if we don't set SETTINGS_MODULE.
                SETTINGS_MODULE='fjord.settings',
                CACHES={
                    'default': {
                        'BACKEND': 'caching.backends.memcached.CacheClass',
                        'LOCATION': ['localhost:11211', 'localhost2:11211']
                        }
                    }):

                views.test_memcached = lambda host, port: True
                resp = self.client.get(reverse('services-monitor'))
                eq_(resp.status_code, 200)

        finally:
            views.test_memcached = test_memcached
