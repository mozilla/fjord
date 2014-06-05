from unittest import TestCase

from django.test.utils import override_settings

from mock import MagicMock, patch
from nose.tools import eq_

from ..utils import translate
from fjord.base.tests import TestCase as FjordTestCase
from fjord.translations import gengo_utils
from fjord.translations.models import SuperModel


class GeneralTranslateTests(TestCase):
    def setUp(self):
        gengo_utils.GENGO_LANGUAGE_CACHE = (
            {u'opstat': u'ok',
             u'response': [
                 {u'unit_type': u'word', u'localized_name': u'Espa\xf1ol',
                  u'lc': u'es', u'language': u'Spanish (Spain)'}
             ]},
            (u'es',)
        )

    def test_translate_fake(self):
        obj = SuperModel(locale='br', desc=u'This is a test string')
        obj.save()

        eq_(obj.trans_desc, u'')
        translate(obj, 'fake', 'br', 'desc', 'en-US', 'trans_desc')
        eq_(obj.trans_desc, u'THIS IS A TEST STRING')

    def test_translate_dennis(self):
        obj = SuperModel(locale='fr', desc=u'This is a test string')
        obj.save()

        eq_(obj.trans_desc, u'')
        translate(obj, 'dennis', 'br', 'desc', 'en-US', 'trans_desc')
        eq_(obj.trans_desc, u'\xabTHIS IS A TEST STRING\xbb')


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

                obj = SuperModel(locale='es', desc=u'Muy lento')
                obj.save()

                eq_(obj.trans_desc, u'')
                translate(obj, 'gengo_machine', 'es', 'desc', 'en-US', 'trans_desc')
                eq_(obj.trans_desc, u'Very slow')

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

                obj = SuperModel(locale='es', desc=u'Muy lento')
                obj.save()

                eq_(obj.trans_desc, u'')
                translate(obj, 'gengo_machine', 'es', 'desc', 'en-US',
                          'trans_desc')
                eq_(obj.trans_desc, u'')

                # Make sure we don't call postTranslationJobs().
                eq_(gengo_mock_instance.postTranslationJobs.call_count, 0)

    def test_translate_gengo_machine_unsupported_language(self):
        """Translation should handle unsupported languages without erroring"""
        gengo_utils.GENGO_LANGUAGE_CACHE = [u'de']
        gengo_utils.GENGO_LANGUAGE_CACHE = (
            {u'opstat': u'ok',
             u'response': [
                 {u'unit_type': u'word', u'localized_name': u'Deutsch',
                  u'lc': u'de', u'language': u'German'}
             ]},
            (u'de',)
        )

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

                obj = SuperModel(locale='es', desc=u'Muy lento')
                obj.save()

                eq_(obj.trans_desc, u'')
                translate(obj, 'gengo_machine', 'es', 'desc', 'en-US',
                          'trans_desc')
                eq_(obj.trans_desc, u'')

                # Make sure we don't call postTranslationJobs().
                eq_(gengo_mock_instance.postTranslationJobs.call_count, 0)
