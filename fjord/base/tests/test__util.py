# -*- coding: utf-8 -*-
from datetime import datetime

from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.base.util import smart_truncate, smart_int, smart_datetime


def test_smart_truncate():
    eq_(smart_truncate(u''), u'')
    eq_(smart_truncate(u'abc'), u'abc')
    eq_(smart_truncate(u'abc def', length=4), u'abc...')
    eq_(smart_truncate(u'abcdef', length=4), u'abcd...')
    eq_(smart_truncate(u'ééé ééé', length=4), u'ééé...')


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


class SmartDateTest(TestCase):
    def test_sanity(self):
        eq_(datetime(2012, 1, 1), smart_datetime('2012-01-01'))
        eq_(datetime(1742, 11, 5), smart_datetime('1742-11-05'))

    def test_empty_string(self):
        eq_(None, smart_datetime(''))

    def test_fallback(self):
        eq_('Hullaballo', smart_datetime('', fallback='Hullaballo'))

    def test_format(self):
        eq_(datetime(2012, 9, 28),
            smart_datetime('9/28/2012', format='%m/%d/%Y'))

    def test_null_bytes(self):
        # strptime likes to barf on null bytes in strings, so test it.
        eq_(None, smart_datetime('/etc/passwd\x00'))
