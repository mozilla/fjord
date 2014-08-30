from nose.tools import eq_

from fjord.base.domain import get_domain
from fjord.base.tests import TestCase


class TestGetDomain(TestCase):
    def test_get_domain(self):
        testdata = [
            # URLs with good domains
            (u'foo.example.com', u'example.com'),
            (u'http://example.com/', u'example.com'),
            (u'http://foo.example.com', u'example.com'),
            (u'http://foo.example.com/', u'example.com'),
            (u'http://foo.example.com:8000/bar/?foo=bar#foobar',
             u'example.com'),
            (u'https://foo.bar.baz.example.com/', u'example.com'),
            (u'example.com.br', u'example.com.br'),
            (u'foo.example.com.br', u'example.com.br'),
            (u'https://foo.example.com.br/', u'example.com.br'),
            (u'http://blog.goo.ne.jp/shinsburger', u'goo.ne.jp'),

            # FIXME - This fails in the tests. See if this works when we
            # change the code to get the most recent tld list from Mozilla.
            # (u'http://500px.com\u6253\u4e0d\u5f00/',
            #  u'500px.com\u6253\u4e0d\u5f00'),

            # URLs with domains we don't like
            (None, u''),
            (u'', u''),
            (u'about:home', u''),
            (u'chrome://whatever', u''),
            (u'127.0.0.1', u''),
            (u'ftp://blah@example.com', u''),
            (u'155.39.97.145.in-addr.arpa', u''),
            (u'example.mil', u''),
            (u'localhost', u''),
        ]

        for data, expected in testdata:
            eq_(get_domain(data), expected)
