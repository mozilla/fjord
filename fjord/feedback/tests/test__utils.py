from django.test.client import RequestFactory

from nose.tools import eq_, ok_

from fjord.base.tests import TestCase, reverse
from fjord.feedback.utils import actual_ip_plus_desc, clean_url, compute_grams


class Testactual_ip_plus_desc(TestCase):
    def test_valid_key(self):
        """Make sure the key is valid"""
        url = reverse('feedback')
        factory = RequestFactory(HTTP_X_CLUSTER_CLIENT_IP='192.168.100.101')

        # create a request with this as the description
        desc = u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e' * 16
        req = factory.post(url, {
            'description': desc
        })
        key = actual_ip_plus_desc(req)

        # Key can't exceed memcached 250 character max
        length = len(key)
        ok_(length < 250)

        # Key must be a string
        ok_(isinstance(key, str))

        # create a request with this as the description
        second_desc = u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d' * 16
        second_req = factory.post(url, {
            'description': second_desc
        })
        second_key = actual_ip_plus_desc(second_req)

        # Two descriptions with the same ip address should produce
        # different keys.
        assert key != second_key

    def test_valid_key_ipv6(self):
        """Make sure ipv6 keys work"""
        url = reverse('feedback')
        factory = RequestFactory(
            HTTP_X_CLUSTER_CLIENT_IP='0000:0000:0000:0000:0000:0000:0000:0000')

        # create a request with this as the description
        desc = u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e' * 16
        req = factory.post(url, {
            'description': desc
        })
        key = actual_ip_plus_desc(req)

        # Key can't exceed memcached 250 character max
        length = len(key)
        ok_(length < 250)


class Testclean_url(TestCase):
    def test_basic(self):
        data = [
            (None, None),
            ('', ''),
            ('http://example.com/', 'http://example.com/'),
            ('http://example.com/#foo', 'http://example.com/'),
            ('http://example.com/?foo=bar', 'http://example.com/'),
            ('http://example.com:8000/', 'http://example.com/'),
            ('ftp://foo.bar/', ''),
            ('chrome://something', 'chrome://something'),
            ('about:home', 'about:home'),
        ]

        for url, expected in data:
            eq_(clean_url(url), expected)


class TestComputeGrams(TestCase):
    # FIXME - Beef this up so that we have more comprehensive tests of the various
    # tokenizing edge cases.

    def test_basic(self):
        test_data = [
            ('The quick brown fox', [u'brown quick', u'brown fox']),

            ('the latest update disables the New tab function',
             [u'disables new', u'function tab', u'new tab', u'latest update',
              u'disables update']),

            ('why is firefox so damn slow???? many tabs load slow or not at '
             'all!',
             [u'load tabs', u'load slow', u'slow tabs', u'damn slow']),

            ("I'm one of the guys that likes to try Firefox ahead of the "
             "herd... usually I use Nightly, but then a while back my "
             "favorite add-on, TabMixPlus stopped working because Firefox "
             "redid something in the code. \"No problem,\" says I to myself, "
             "I'll just use Aurora until they get it fixed.",
             [u'add-on favorite', u'add-on tabmixplus', u'ahead herd',
              u'ahead try', u'aurora fixed', u'aurora use', u'code problem',
              u'code redid', u'favorite nightly', u"guys i'm", u'guys likes',
              u'herd usually', u"i'll just", u"i'll myself", u'just use',
              u'likes try', u'myself says', u'nightly use', u'problem says',
              u'redid working', u'stopped tabmixplus', u'stopped working',
              u'use usually']),

            ('Being partially sighted, I found the features with Windows XP '
             'and IE8 extremely usefu;. I need everything in Arial black bold '
             'text.',
             [u'extremely usefu', u'features sighted', u'windows xp', u'ie8 xp',
              u'black bold', u'partially sighted', u'need usefu',
              u'features windows', u'arial need', u'arial black', u'bold text',
              u'extremely ie8']),
        ]

        for text, expected in test_data:
            eq_(sorted(compute_grams(text)), sorted(expected))
