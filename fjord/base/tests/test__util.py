# -*- coding: utf-8 -*-
import datetime

from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.base.util import (
    instance_to_key,
    key_to_instance,
    smart_bool,
    smart_date,
    smart_int,
    smart_str,
    smart_truncate
)


def test_smart_truncate():
    eq_(smart_truncate(u''), u'')
    eq_(smart_truncate(u'abc'), u'abc')
    eq_(smart_truncate(u'abc def', length=4), u'abc...')
    eq_(smart_truncate(u'abcdef', length=4), u'abcd...')
    eq_(smart_truncate(u'ééé ééé', length=4), u'ééé...')


class SmartStrTestCase(TestCase):
    def test_str(self):
        eq_('a', smart_str('a'))
        eq_(u'a', smart_str(u'a'))

    def test_not_str(self):
        eq_(u'', smart_str(1))
        eq_(u'', smart_str(1.1))
        eq_(u'', smart_str(True))
        eq_(u'', smart_str(['a']))

        eq_(u'', smart_str(None))


class SmartIntTestCase(TestCase):
    def test_sanity(self):
        eq_(10, smart_int('10'))
        eq_(10, smart_int('10.5'))

    def test_int(self):
        eq_(10, smart_int(10))

    def test_invalid_string(self):
        eq_(0, smart_int('invalid'))

    def test_empty_string(self):
        eq_(0, smart_int(''))

    def test_wrong_type(self):
        eq_(0, smart_int(None))
        eq_(10, smart_int([], 10))

    def test_overflow(self):
        eq_(0, smart_int('1e309'))


class SmartDateTest(TestCase):
    def test_sanity(self):
        eq_(datetime.date(2012, 1, 1), smart_date('2012-01-01'))
        eq_(None, smart_date('1742-11-05'))
        eq_(None, smart_date('0001-01-01'))

    def test_empty_string(self):
        eq_(None, smart_date(''))

    def test_date(self):
        eq_(datetime.date(2012, 1, 1), smart_date('2012-01-01'))
        eq_(datetime.date(2012, 1, 1), smart_date('2012-1-1'))

    def test_fallback(self):
        eq_('Hullaballo', smart_date('', fallback='Hullaballo'))

    def test_null_bytes(self):
        # strptime likes to barf on null bytes in strings, so test it.
        eq_(None, smart_date('/etc/passwd\x00'))


class SmartBoolTest(TestCase):

    msg_template = 'smart_bool(%r) - Expected %r, got %r'

    def test_truthy(self):
        truths = ['Yes', 'y', u'TRUE', '1', u'1']
        for x in truths:
            b = smart_bool(x, 'fallback')
            assert b == True, self.msg_template % (x, True, b)

    def test_falsey(self):
        falses = ['No', 'n', u'FALSE', '0', u'0']
        for x in falses:
            b = smart_bool(x, 'fallback')
            assert b == False, self.msg_template % (x, False, b)

    def test_fallback(self):
        garbages = [None, 'apple', u'']
        for x in garbages:
            b = smart_bool(x, 'fallback')
            assert b == 'fallback', self.msg_template % (x, 'fallback', b)


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
        eq_(instance_to_key(foo), 'fjord.base.tests.test__util:FakeModel:15')

    def test_key_to_instance(self):
        foo = FakeModel(15)
        key = 'fjord.base.tests.test__util:FakeModel:15'
        eq_(key_to_instance(key), foo)
