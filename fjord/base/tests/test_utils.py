# -*- coding: utf-8 -*-
import datetime

from django.test.client import RequestFactory

from fjord.base.tests import reverse, TestCase
from fjord.base.utils import (
    actual_ip_plus_context,
    instance_to_key,
    key_to_instance,
    smart_bool,
    smart_date,
    smart_int,
    smart_str,
    smart_timedelta,
    smart_truncate,
    wrap_with_paragraphs,
)


def test_smart_truncate():
    assert smart_truncate(u'') == u''
    assert smart_truncate(u'abc') == u'abc'
    assert smart_truncate(u'abc def', length=4) == u'abc...'
    assert smart_truncate(u'abcdef', length=4) == u'abcd...'
    assert smart_truncate(u'ééé ééé', length=4) == u'ééé...'


class SmartStrTestCase(TestCase):
    def test_str(self):
        assert 'a' == smart_str('a')
        assert u'a' == smart_str(u'a')

    def test_not_str(self):
        assert u'' == smart_str(1)
        assert u'' == smart_str(1.1)
        assert u'' == smart_str(True)
        assert u'' == smart_str(['a'])

        assert u'' == smart_str(None)


class SmartIntTestCase(TestCase):
    def test_sanity(self):
        assert 10 == smart_int('10')
        assert 10 == smart_int('10.5')

    def test_int(self):
        assert 10 == smart_int(10)

    def test_invalid_string(self):
        assert 0 == smart_int('invalid')

    def test_empty_string(self):
        assert 0 == smart_int('')

    def test_wrong_type(self):
        assert 0 == smart_int(None)
        assert 10 == smart_int([], 10)

    def test_overflow(self):
        assert 0 == smart_int('1e309')


class SmartDateTest(TestCase):
    def test_sanity(self):
        assert datetime.date(2012, 1, 1) == smart_date('2012-01-01')
        assert None == smart_date('1742-11-05')
        assert None == smart_date('0001-01-01')

    def test_empty_string(self):
        assert None == smart_date('')

    def test_date(self):
        assert datetime.date(2012, 1, 1) == smart_date('2012-01-01')
        assert datetime.date(2012, 1, 1) == smart_date('2012-1-1')

    def test_fallback(self):
        assert 'Hullaballo' == smart_date('', fallback='Hullaballo')

    def test_null_bytes(self):
        # strptime likes to barf on null bytes in strings, so test it.
        assert None == smart_date('/etc/passwd\x00')


class SmartBoolTest(TestCase):

    msg_template = 'smart_bool(%r) - Expected %r, got %r'

    def test_truthy(self):
        truths = ['Yes', 'y', u'TRUE', '1', u'1']
        for x in truths:
            b = smart_bool(x, 'fallback')
            assert b is True, self.msg_template % (x, True, b)

    def test_falsey(self):
        falses = ['No', 'n', u'FALSE', '0', u'0']
        for x in falses:
            b = smart_bool(x, 'fallback')
            assert b is False, self.msg_template % (x, False, b)

    def test_fallback(self):
        garbages = [None, 'apple', u'']
        for x in garbages:
            b = smart_bool(x, 'fallback')
            assert b == 'fallback', self.msg_template % (x, 'fallback', b)


class SmartTimeDeltaTest(TestCase):
    def test_valid(self):
        assert smart_timedelta('1d') == datetime.timedelta(days=1)
        assert smart_timedelta('14d') == datetime.timedelta(days=14)

    def test_invalid(self):
        assert smart_timedelta('0d', 'fallback') == 'fallback'
        assert smart_timedelta('foo', 'fallback') == 'fallback'
        assert smart_timedelta('d', 'fallback') == 'fallback'


class WrapWithParagraphsTest(TestCase):
    def test_basic(self):
        test_data = [
            ('', 72, ''),
            ('abc', 72, 'abc'),
            ('abc\ndef', 72, 'abc\ndef'),
            ('abc def ghi jkl\nfoo bar\nbaz', 8,
             'abc def\nghi jkl\nfoo bar\nbaz'),
        ]

        for arg, width, expected in test_data:
            assert wrap_with_paragraphs(arg, width) == expected

    def test_edge_cases(self):
        test_data = [
            (None, 72, None),
            ('abcdefghijkl\nfoo bar', 8, 'abcdefgh\nijkl\nfoo bar'),
        ]

        for arg, width, expected in test_data:
            assert wrap_with_paragraphs(arg, width) == expected


_foo_cache = {}


class FakeModelManager(object):
    def get(self, **kwargs):
        return _foo_cache[kwargs['pk']]


class FakeModel(object):
    def __init__(self, pk):
        self.pk = pk
        _foo_cache[pk] = self

    def __repr__(self):
        return '<FakeModel:{0}>'.format(self.pk)

    objects = FakeModelManager()


class TestKeys(TestCase):
    def tearDown(self):
        _foo_cache.clear()

    def test_instance_to_key(self):
        foo = FakeModel(15)
        key = 'fjord.base.tests.test_utils:FakeModel:15'
        assert instance_to_key(foo) == key

    def test_key_to_instance(self):
        foo = FakeModel(15)
        key = 'fjord.base.tests.test_utils:FakeModel:15'
        assert key_to_instance(key) == foo


class TestActualIPPlusContext(TestCase):
    def test_valid_key(self):
        """Make sure the key is valid"""
        actual_ip_plus_desc = actual_ip_plus_context(
            lambda req: req.POST.get('description', 'no description')
        )

        url = reverse('feedback')
        factory = RequestFactory(HTTP_X_CLUSTER_CLIENT_IP='192.168.100.101')

        # create a request with this as the description
        desc = u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e' * 16
        req = factory.post(url, {
            'description': desc
        })
        key = actual_ip_plus_desc('foogroup', req)

        # Key can't exceed memcached 250 character max
        length = len(key)
        assert length < 250

        # Key must be a string
        assert isinstance(key, str)

        # create a request with this as the description
        second_desc = u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d' * 16
        second_req = factory.post(url, {
            'description': second_desc
        })
        second_key = actual_ip_plus_desc('foogroup', second_req)

        # Two descriptions with the same ip address should produce
        # different keys.
        assert key != second_key

    def test_valid_key_ipv6(self):
        """Make sure ipv6 keys work"""
        actual_ip_plus_desc = actual_ip_plus_context(
            lambda req: req.POST.get('description', 'no description')
        )

        url = reverse('feedback')
        factory = RequestFactory(
            HTTP_X_CLUSTER_CLIENT_IP='0000:0000:0000:0000:0000:0000:0000:0000')

        # create a request with this as the description
        desc = u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e' * 16
        req = factory.post(url, {
            'description': desc
        })
        key = actual_ip_plus_desc('foogroup', req)

        # Key can't exceed memcached 250 character max
        length = len(key)
        assert length < 250
