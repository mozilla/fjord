from unittest import TestCase

from nose.tools import eq_

from . import fakeinstance
from ..utils import compose_key, decompose_key, translate


_foo_cache = {}


class FakeModelManager(object):
    def get(self, **kwargs):
        return _foo_cache[kwargs['id']]


class FakeModel(object):
    def __init__(self, id_):
        self.id = id_
        _foo_cache[id_] = self

    objects = FakeModelManager()


class TestKeys(TestCase):
    def tearDown(self):
        _foo_cache.clear()

    def test_compose_key(self):
        foo = FakeModel(15)
        eq_(compose_key(foo), 'fjord.translations.tests.test__utils:FakeModel:15')

    def test_decompose_key(self):
        foo = FakeModel(15)
        key = 'fjord.translations.tests.test__utils:FakeModel:15'
        eq_(decompose_key(key), foo)


class TestTranslate(TestCase):
    def test_translate_fake(self):
        obj = fakeinstance(
            fields={'desc': 'trans_desc'},
            translate_with=lambda x: 'fake',
            desc=u'This is a test string'
        )
        eq_(getattr(obj, 'trans_desc', None), None)
        translate(obj, 'fake', 'br', 'desc', 'en-US', 'trans_desc')
        eq_(getattr(obj, 'trans_desc', None), u'THIS IS A TEST STRING')

    def test_translate_dennis(self):
        obj = fakeinstance(
            fields={'desc': 'trans_desc'},
            translate_with=lambda x: 'dennis',
            desc=u'This is a test string'
        )
        eq_(getattr(obj, 'trans_desc', None), None)
        translate(obj, 'dennis', 'br', 'desc', 'en-US', 'trans_desc')
        eq_(getattr(obj, 'trans_desc', None),
            u'\xabTHIS IS A TEST STRING\xbb')
