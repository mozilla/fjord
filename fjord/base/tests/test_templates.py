from fjord.base.middleware import MOBILE_COOKIE
from nose.tools import eq_

from fjord.base.tests import LocalizingClient, reverse
from fjord.search.tests import ElasticTestCase


# This is an ElasticTestCase instead of a normal one because the front page
# (which this queries) uses elastic search. Being an ElasticTestCase makes
# sure that the testing index is properly set up, instead of trying to access
# a possibly missing index.
class MobileQueryStringOverrideTest(ElasticTestCase):
    client_class = LocalizingClient

    def test_mobile_override(self):
        # Doing a request without specifying a mobile querystring
        # parameter should not set a cookie.
        resp = self.client.get(reverse('home_view'))
        assert MOBILE_COOKIE not in resp.cookies

        # Doing a request and specifying the mobile querystring
        # parameter should persist that value in the MOBILE cookie.
        resp = self.client.get(reverse('home_view'), {
                'mobile': 1
                })
        assert MOBILE_COOKIE in resp.cookies
        eq_(resp.cookies[MOBILE_COOKIE].value, 'yes')

        resp = self.client.get(reverse('home_view'), {
                'mobile': 0
                })
        assert MOBILE_COOKIE in resp.cookies
        eq_(resp.cookies[MOBILE_COOKIE].value, 'no')
