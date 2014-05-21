from unittest import TestCase

from django.test.utils import override_settings

from mock import MagicMock, patch
from nose.tools import eq_

from . import fakeinstance
from ..utils import compose_key, decompose_key, translate
from fjord.translations import gengo_utils
from fjord.base.tests import TestCase as FjordTestCase


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


class GeneralTranslateTests(TestCase):
    def setUp(self):
        gengo_utils.GENGO_LANGUAGE_CACHE = [u'es']

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


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class GengoMachineTests(FjordTestCase):
    def test_translate_gengo_machine(self):
        with patch('fjord.translations.gengo_utils.requests') as requests_mock:
            post_return = MagicMock()
            post_return.json.return_value = {
                u'text_bytes_found': 40,
                u'opstat': u'ok',
                u'is_reliable': False,
                u'detected_lang_code': u'es',
                u'details': [
                    [u'SPANISH', u'es', 62, 46.728971962616825],
                    [u'ITALIAN', u'it', 38, 9.237875288683602]
                ],
                u'detected_lang_name': u'SPANISH'
            }
            requests_mock.post.return_value = post_return

            with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
                # Note: We're mocking with "Muy lento" because it's
                # short, but the Gengo language guesser actually can't
                # figure out what language that is.
                instance = GengoMock.return_value
                instance.postTranslationJobs.return_value = {
                    u'opstat': u'ok',
                    u'response': {
                        u'jobs': {
                            u'job_1': {
                                u'status': u'approved',
                                u'job_id': u'NULL',
                                u'credits': 0,
                                u'unit_count': 7,
                                u'body_src': u'Muy lento',
                                u'mt': 1,
                                u'eta': -1,
                                u'custom_data': u'10101',
                                u'tier': u'machine',
                                u'lc_tgt': u'en',
                                u'lc_src': u'es',
                                u'body_tgt': u'Very slow',
                                u'slug': u'Input machine translation',
                                u'ctime': u'2014-05-21 15:09:50.361847'
                            }
                        }
                    }
                }

                obj = fakeinstance(
                    id=10101,
                    fields={'desc': 'trans_desc'},
                    translate_with=lambda x: 'gengo_machine',
                    desc=u'Muy lento'
                )
                eq_(getattr(obj, 'trans_desc', None), None)
                translate(obj, 'gengo_machine', 'es', 'desc', 'en-US', 'trans_desc')
                eq_(getattr(obj, 'trans_desc', None), u'Very slow')

    def test_translate_gengo_machine_unknown_language(self):
        """Translation should handle unknown languages without erroring"""
        with patch('fjord.translations.gengo_utils.requests') as requests_mock:
            post_return = MagicMock()
            post_return.json.return_value = {
                u'text_bytes_found': 10,
                u'opstat': u'ok',
                u'is_reliable': True,
                u'detected_lang_code': u'un',
                u'details': [],
                u'detected_lang_name': u'Unknown'
            }
            requests_mock.post.return_value = post_return

            with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
                gengo_mock_instance = GengoMock.return_value

                obj = fakeinstance(
                    id=10101,
                    fields={'desc': 'trans_desc'},
                    translate_with=lambda x: 'gengo_machine',
                    desc=u'Muy lento'
                )
                eq_(getattr(obj, 'trans_desc', None), None)
                translate(obj, 'gengo_machine', 'es', 'desc', 'en-US',
                          'trans_desc')
                eq_(getattr(obj, 'trans_desc', None), None)

                # Make sure we don't call postTranslationJobs().
                eq_(gengo_mock_instance.postTranslationJobs.call_count, 0)

    def test_translate_gengo_machine_unsupported_language(self):
        """Translation should handle unsupported languages without erroring"""
        gengo_utils.GENGO_LANGUAGE_CACHE = [u'de']

        with patch('fjord.translations.gengo_utils.requests') as requests_mock:
            post_return = MagicMock()
            post_return.json.return_value = {
                u'text_bytes_found': 40,
                u'opstat': u'ok',
                u'is_reliable': False,
                u'detected_lang_code': u'es',
                u'details': [
                    [u'SPANISH', u'es', 62, 46.728971962616825],
                    [u'ITALIAN', u'it', 38, 9.237875288683602]
                ],
                u'detected_lang_name': u'SPANISH'
            }
            requests_mock.post.return_value = post_return

            with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
                gengo_mock_instance = GengoMock.return_value

                obj = fakeinstance(
                    id=10101,
                    fields={'desc': 'trans_desc'},
                    translate_with=lambda x: 'gengo_machine',
                    desc=u'Muy lento'
                )
                eq_(getattr(obj, 'trans_desc', None), None)
                translate(obj, 'gengo_machine', 'es', 'desc', 'en-US',
                          'trans_desc')
                eq_(getattr(obj, 'trans_desc', None), None)

                # Make sure we don't call postTranslationJobs().
                eq_(gengo_mock_instance.postTranslationJobs.call_count, 0)
