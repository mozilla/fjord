from fjord.base.tests import TestCase, LocalizingClient, reverse
from mobility.middleware import COOKIE as MOBILE_COOKIE
from nose.tools import eq_


class MobileQueryStringOverrideTest(TestCase):
    client_class = LocalizingClient

    def test_mobile_override(self):
        # Doing a request without the mobile querystring parameter
        # shouldn't try to persist the mobile-ness in a cookie.
        resp = self.client.get(reverse('home_view'))
        assert MOBILE_COOKIE not in resp.cookies

        # Doing a request and specifying the mobile querystring
        # parameter should persist that value in the MOBILE cookie.
        resp = self.client.get(reverse('home_view'), {
                'mobile': 1
                })
        eq_(resp.cookies[MOBILE_COOKIE].value, 'on')

        resp = self.client.get(reverse('home_view'), {
                'mobile': 0
                })
        eq_(resp.cookies[MOBILE_COOKIE].value, 'off')

