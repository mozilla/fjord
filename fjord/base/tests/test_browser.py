import json
import os

from django import test

from nose.tools import eq_

from fjord.base import browsers, middleware


class TestUserAgentDetection(object):

    def check_ua(self, case):
        """Check and individual user agent test case."""
        parsed = browsers.parse_ua(case['user_agent'])
        assert(parsed is not None)

        expected = tuple(case[key] for key in
                         ['browser', 'browser_version',
                          'platform', 'platform_version',
                          'mobile'])

        eq_(parsed, expected)

    def test_parse_ua(self):
        """Test that a suite of should-work user agents work."""
        path = os.path.join(os.path.dirname(__file__), 'user_agent_data.json')
        with open(path) as f:
            cases = f.read()
        cases = json.loads(cases)
        for case in cases:
            self.check_ua(case)

    def test_error_handling(self):
        """Make sure that good, bad, and ugly UAs don't break the parser."""
        path = os.path.join(os.path.dirname(__file__), 'bad_user_agents.txt')
        with open(path) as f:
            for ua in f:
                browsers.parse_ua(ua)

    def test_middleware(self):
        """Check that the middleware injects data properly."""
        ua = "Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0.2"
        d = {
            'HTTP_USER_AGENT': ua,
        }
        request = test.RequestFactory().get('/', **d)
        ret = middleware.UserAgentMiddleware().process_request(request)
        assert ret is None

        checks = {
            'browser': 'Firefox',
            'browser_version': '14.0.2',
            'platform': 'Android',
            'platform_version': None,
            'mobile': True,
        }

        assert(hasattr(request, 'BROWSER'))
        for k, v in checks.items():
            assert(hasattr(request.BROWSER, k))
            eq_(getattr(request.BROWSER, k), v)
