from test_utils import TestCase
from nose.tools import eq_

from fjord import browsers


class TestUserAgentDetection(object):

    def test_parse_ua(self):
        for case in cases:
            yield self.check_ua, case

    def check_ua(cls, case):
        parsed = browsers.parse_ua(case['useragent'])

        keys = ['browser', 'browser_version',
                'platform', 'platform_version',
                'mobile']

        for key in keys:
            eq_(parsed[key], case[key])


cases = [
    # Add manually
    {   # Mike's phone
        'useragent': 'Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0.2',
        'browser': 'Firefox',
        'browser_version': '14.0.2',
        'platform': 'Android',
        'platform_version': None,
        'mobile': True,
    },
    # Derived from the user agents at
    # http://techpatterns.com/forums/about304.html
    {
        'useragent': 'Mozilla/5.0 (OS X; Intel Mac OS X 10.5; rv:10.0.1) Gecko/20100101 Firefox/10.0.1 SeaMonkey/2.7.1',
        'browser': 'Firefox',
        'browser_version': '10.0.1',
        'platform': 'OS X',
        'platform_version': '10.5',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (OS X; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'browser': 'Firefox',
        'browser_version': '4.0.1',
        'platform': 'OS X',
        'platform_version': '10.6',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (OS X; Intel Mac OS X 10.6; rv:5.0) Gecko/20100101 Firefox/5.0',
        'browser': 'Firefox',
        'browser_version': '5.0.0',
        'platform': 'OS X',
        'platform_version': '10.6',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (OS X; Intel Mac OS X 10.6; rv:9.0) Gecko/20100101 Firefox/9.0',
        'browser': 'Firefox',
        'browser_version': '9.0.0',
        'platform': 'OS X',
        'platform_version': '10.6',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (OS X; Intel Mac OS X 10_7_2; rv:10.0.1) Gecko/20100101 Firefox/10.0.1',
        'browser': 'Firefox',
        'browser_version': '10.0.1',
        'platform': 'OS X',
        'platform_version': '10.7.2',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0',
        'browser': 'Firefox',
        'browser_version': '5.0.0',
        'platform': 'Windows',
        'platform_version': 'XP',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (Windows NT 5.2; rv:10.0.1) Gecko/20100101 Firefox/10.0.1 SeaMonkey/2.7.1',
        'browser': 'Firefox',
        'browser_version': '10.0.1',
        'platform': 'Windows',
        'platform_version': 'XP',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1',
        'browser': 'Firefox',
        'browser_version': '14.0.1',
        'platform': 'Windows',
        'platform_version': 'Vista',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.1) Gecko/20100101 Firefox/10.0.1',
        'browser': 'Firefox',
        'browser_version': '10.0.1',
        'platform': 'Windows',
        'platform_version': '7',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
        'browser': 'Firefox',
        'browser_version': '7.0.1',
        'platform': 'Windows',
        'platform_version': '7',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'browser': 'Firefox',
        'browser_version': '4.0.1',
        'platform': 'Windows',
        'platform_version': '7',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (Windows NT 6.1; rv:12.0) Gecko/20120403211507 Firefox/12.0',
        'browser': 'Firefox',
        'browser_version': '12.0.0',
        'platform': 'Windows',
        'platform_version': '7',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'browser': 'Firefox',
        'browser_version': '4.0.1',
        'platform': 'Windows',
        'platform_version': '7',
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (WindowsCE 6.0; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'browser': 'Firefox',
        'browser_version': '4.0.1',
        'platform': 'Windows',
        'platform_version': 'CE',
        'mobile': True,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; FreeBSD amd64; rv:5.0) Gecko/20100101 Firefox/5.0',
        'browser': 'Firefox',
        'browser_version': '5.0.0',
        'platform': 'FreeBSD',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux i686 on x86_64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'browser': 'Firefox',
        'browser_version': '4.0.1',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0 ',
        'browser': 'Firefox',
        'browser_version': '12.0.0',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux i686; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'browser': 'Firefox',
        'browser_version': '4.0.1',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0',
        'browser': 'Firefox',
        'browser_version': '5.0.0',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/6.0',
        'browser': 'Firefox',
        'browser_version': '6.0.0',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
        'browser': 'Firefox',
        'browser_version': '8.0.0',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0.1) Gecko/20100101 Firefox/10.0.1',
        'browser': 'Firefox',
        'browser_version': '10.0.1',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux x86_64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'browser': 'Firefox',
        'browser_version': '4.0.1',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Linux x86_64; rv:5.0) Gecko/20100101 Firefox/5.0 Iceweasel/5.0',
        'browser': 'Iceweasel',
        'browser_version': '5.0.0',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.16) Gecko/20120421 Gecko Firefox/11.0',
        'browser': 'Firefox',
        'browser_version': '11.0.0',
        'platform': 'Linux',
        'platform_version': None,
        'mobile': False,
    },
    {
        'useragent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
        'browser': 'Firefox',
        'browser_version': '14.0.1',
        'platform': 'Linux',
        'platform_version': 'Ubuntu',
        'mobile': False,
    }
]
