import json
import os
from nose.tools import eq_

from fjord import browsers


class TestUserAgentDetection(object):

    def test_parse_ua(self):
        path = os.path.join(os.path.dirname(__file__), 'user_agent_data.json')
        with open(path) as f:
            cases = f.read()
        cases = json.loads(cases)
        for case in cases:
            self.check_ua(case)

    def test_error_handling(self):
        path = os.path.join(os.path.dirname(__file__), 'bad_useragents.txt')
        with open(path) as f:
            for ua in f:
                self.check_error_handling(ua)

    def check_ua(cls, case):
        parsed = browsers.parse_ua(case['useragent'])
        assert(parsed is not None)

        keys = ['browser', 'browser_version',
                'platform', 'platform_version',
                'mobile']

        for key in keys:
            eq_(parsed[key], case[key])

    def check_error_handling(cls, ua):
        # This should not raise an exception.
        browsers.parse_ua(ua)
