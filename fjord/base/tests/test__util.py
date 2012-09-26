# -*- coding: utf-8 -*-
from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.base.util import smart_truncate, smart_int


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
