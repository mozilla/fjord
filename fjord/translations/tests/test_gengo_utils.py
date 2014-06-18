from django.conf import settings
from django.test.utils import override_settings

from mock import MagicMock, patch
from nose.tools import eq_

from fjord.base.tests import TestCase, skip_if, has_environ_variable
from fjord.translations import gengo_utils


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class GengoTestCase(TestCase):
    def setUp(self):
        gengo_utils.GENGO_LANGUAGE_CACHE = (
            {u'opstat': u'ok',
             u'response': [
                 {u'unit_type': u'word', u'localized_name': u'Espa\xf1ol',
                  u'lc': u'es', u'language': u'Spanish (Spain)'}
             ]},
            (u'es',)
        )
        super(GengoTestCase, self).setUp()

    def test_guess_language_throws_error(self):
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

            gengo_api = gengo_utils.FjordGengo()
            self.assertRaises(
                gengo_utils.GengoUnknownLanguage,
                gengo_api.guess_language,
                u'Muy lento',
            )

    def test_guess_language_returns_language(self):
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

            gengo_api = gengo_utils.FjordGengo()
            text = u'Facebook no se puede enlazar con peru'
            eq_(gengo_api.guess_language(text), u'es')

    def test_get_languages(self):
        response = {
            u'opstat': u'ok',
            u'response': [
                {u'unit_type': u'word', u'localized_name': u'Espa\xf1ol',
                 u'lc': u'es', u'language': u'Spanish (Spain)'}
            ]
        }

        gengo_utils.GENGO_LANGUAGE_CACHE = None

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            # Note: We're mocking with "Muy lento" because it's
            # short, but the Gengo language guesser actually can't
            # figure out what language that is.
            instance = GengoMock.return_value
            instance.getServiceLanguages.return_value = response

            # Make sure the cache is empty
            eq_(gengo_utils.GENGO_LANGUAGE_CACHE, None)

            # Test that we generate a list based on what we think the
            # response is.
            gengo_api = gengo_utils.FjordGengo()
            eq_(gengo_api.get_languages(), (u'es',))

            # Test that the new list is cached.
            eq_(gengo_utils.GENGO_LANGUAGE_CACHE, (response, (u'es',)))

    def test_machine_translation(self):
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

                gengo_api = gengo_utils.FjordGengo()
                text = u'Muy lento'
                eq_(gengo_api.get_machine_translation(1010, 'es', 'en', text),
                    u'Very slow')


def has_gengo_creds():
    """Returns True if there are GENGO credentials set

    Note: This doesn't verify the credentials--just checks to see if
    they are set.

    """
    return settings.GENGO_PUBLIC_KEY and settings.GENGO_PRIVATE_KEY


@skip_if(lambda: not has_gengo_creds())
class GengoNoMocksTestCase(TestCase):
    """Holds LIVE test cases that execute REAL Gengo calls

    These tests require GENGO_PUBLIC_KEY and GENGO_PRIVATE_KEY to be
    valid values in your settings_local.py file.

    Please don't fake the credentials since then you'll just get API
    authentication errors.

    """
    def setUp(self):
        # Wipe out the GENGO_LANGUAGE_CACHE
        gengo_utils.GENGO_LANGUAGE_CACHE = None
        super(GengoNoMocksTestCase, self).setUp()

    def test_get_language(self):
        text = u'Facebook no se puede enlazar con peru'
        gengo_api = gengo_utils.FjordGengo()
        eq_(gengo_api.guess_language(text), u'es')

    def test_machine_translation(self):
        # Note: This test might be brittle since it's calling out to
        # Gengo to do a machine translation and it's entirely possible
        # that they might return a different translation some day.
        text = u'Facebook no se puede enlazar con peru'
        gengo_api = gengo_utils.FjordGengo()
        eq_(gengo_api.get_machine_translation(1010, 'es', 'en', text),
            u'Facebook can bind with peru')
