from functools import wraps

from django.conf import settings
from django.core import mail
from django.test.utils import override_settings

from mock import MagicMock, patch
from nose.tools import eq_

from fjord.base.tests import TestCase, skip_if
from fjord.translations import gengo_utils
from fjord.translations.models import (
    GengoHumanTranslator,
    GengoJob,
    GengoOrder,
    SuperModel
)
from fjord.translations.tests import has_gengo_creds
from fjord.translations.utils import translate


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class BaseGengoTestCase(TestCase):
    def setUp(self):
        gengo_utils.GENGO_LANGUAGE_CACHE = (
            {u'opstat': u'ok',
             u'response': [
                 {u'unit_type': u'word', u'localized_name': u'Espa\xf1ol',
                  u'lc': u'es', u'language': u'Spanish (Spain)'},
                 {u'unit_type': u'word', u'localized_name': u'Deutsch',
                  u'lc': u'de', u'language': u'German'},
                 {u'unit_type': u'word', u'localized_name': u'English',
                  u'lc': u'en', u'language': u'English'}
             ]},
            (u'es', u'de', u'en')
        )
        super(BaseGengoTestCase, self).setUp()


def account_balance(bal):
    def account_balance_handler(fun):
        @wraps(fun)
        def _account_balance_handler(*args, **kwargs):
            patcher = patch('fjord.translations.gengo_utils.Gengo')
            mocker = patcher.start()

            instance = mocker.return_value
            instance.getAccountBalance.return_value = {
                u'opstat': u'ok',
                u'response': {
                    u'credits': str(bal),
                    u'currency': u'USD'
                }
            }

            try:
                return fun(*args, **kwargs)
            finally:
                patcher.stop()

        return _account_balance_handler
    return account_balance_handler


def guess_language(lang):
    def guess_language_handler(fun):
        @wraps(fun)
        def _guess_language_handler(*args, **kwargs):
            patcher = patch('fjord.translations.gengo_utils.requests')
            mocker = patcher.start()

            post_return = MagicMock()

            ret = {
                u'text_bytes_found': 10,
                u'opstat': u'ok',
                u'is_reliable': True,
            }
            if lang == 'un':
                ret.update({
                    u'detected_lang_code': u'un',
                    u'details': [],
                    u'detected_lang_name': u'Unknown'
                })
            elif lang == 'es':
                ret.update({
                    u'detected_lang_code': u'es',
                    u'details': [
                        [u'SPANISH', u'es', 62, 46.728971962616825],
                        [u'ITALIAN', u'it', 38, 9.237875288683602]
                    ],
                    u'detected_lang_name': u'SPANISH'
                })
            elif lang == 'en':
                ret.update({
                    u'detected_lang_code': u'en',
                    u'details': [
                        [u'ENGLISH', u'en', 62, 46.728971962616825],
                        [u'ITALIAN', u'it', 38, 9.237875288683602]
                    ],
                    u'detected_lang_name': u'ENGLISH'
                })
            post_return.json.return_value = ret
            mocker.post.return_value = post_return

            try:
                return fun(*args, **kwargs)
            finally:
                patcher.stop()

        return _guess_language_handler
    return guess_language_handler


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class GuessLanguageTest(BaseGengoTestCase):
    @guess_language('un')
    def test_guess_language_throws_error(self):
        gengo_api = gengo_utils.FjordGengo()
        self.assertRaises(
            gengo_utils.GengoUnknownLanguage,
            gengo_api.guess_language,
            u'Muy lento',
        )

    @guess_language('es')
    def test_guess_language_returns_language(self):
        gengo_api = gengo_utils.FjordGengo()
        text = u'Facebook no se puede enlazar con peru'
        eq_(gengo_api.guess_language(text), u'es')


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class GetLanguagesTestCase(BaseGengoTestCase):
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


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class GetBalanceTestCase(BaseGengoTestCase):
    @account_balance(20.0)
    def test_get_balance(self):
        gengo_api = gengo_utils.FjordGengo()
        eq_(gengo_api.get_balance(), 20.0)


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class MachineTranslationTestCase(BaseGengoTestCase):
    @guess_language('es')
    def test_machine_translation(self):
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

    @guess_language('es')
    def test_translate_gengo_machine(self):
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
            translate(obj, 'gengo_machine', 'es', 'desc', 'en', 'trans_desc')
            eq_(obj.trans_desc, u'Very slow')

    @guess_language('un')
    def test_translate_gengo_machine_unknown_language(self):
        """Translation should handle unknown languages without erroring"""
        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            gengo_mock_instance = GengoMock.return_value

            obj = SuperModel(locale='es', desc=u'Muy lento')
            obj.save()

            eq_(obj.trans_desc, u'')
            translate(obj, 'gengo_machine', 'es', 'desc', 'en', 'trans_desc')
            eq_(obj.trans_desc, u'')

            # Make sure we don't call postTranslationJobs().
            eq_(gengo_mock_instance.postTranslationJobs.call_count, 0)

    @guess_language('es')
    def test_translate_gengo_machine_unsupported_language(self):
        """Translation should handle unsupported languages without erroring"""
        gengo_utils.GENGO_LANGUAGE_CACHE = (
            {u'opstat': u'ok',
             u'response': [
                 {u'unit_type': u'word', u'localized_name': u'Deutsch',
                  u'lc': u'de', u'language': u'German'}
             ]},
            (u'de',)
        )

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            gengo_mock_instance = GengoMock.return_value

            obj = SuperModel(locale='es', desc=u'Muy lento')
            obj.save()

            eq_(obj.trans_desc, u'')
            translate(obj, 'gengo_machine', 'es', 'desc', 'en', 'trans_desc')
            eq_(obj.trans_desc, u'')

            # Make sure we don't call postTranslationJobs().
            eq_(gengo_mock_instance.postTranslationJobs.call_count, 0)

    @guess_language('en')
    def test_translate_gengo_machine_english_copy_over(self):
        """If the guesser guesses english, we copy it over"""
        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            gengo_mock_instance = GengoMock.return_value

            obj = SuperModel(locale='es', desc=u'This is English.')
            obj.save()

            eq_(obj.trans_desc, u'')
            translate(obj, 'gengo_machine', 'es', 'desc', 'en', 'trans_desc')
            eq_(obj.trans_desc, u'This is English.')

            # Make sure we don't call postTranslationJobs().
            eq_(gengo_mock_instance.postTranslationJobs.call_count, 0)


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class HumanTranslationTestCase(BaseGengoTestCase):
    @guess_language('es')
    def test_translate_gengo_human(self):
        # Note: This just sets up the GengoJob--it doesn't create any
        # Gengo human translation jobs.
        obj = SuperModel(
            locale='es',
            desc=u'Facebook no se puede enlazar con peru'
        )
        obj.save()

        eq_(obj.trans_desc, u'')
        translate(obj, 'gengo_human', 'es', 'desc', 'en', 'trans_desc')
        # Nothing should be translated
        eq_(obj.trans_desc, u'')

        eq_(len(GengoJob.objects.all()), 1)

    @guess_language('en')
    def test_translate_gengo_human_english_copy_over(self):
        obj = SuperModel(
            locale='es',
            desc=u'This is English.'
        )
        obj.save()

        eq_(obj.trans_desc, u'')
        translate(obj, 'gengo_human', 'es', 'desc', 'en', 'trans_desc')
        # If the guesser guesses English, then we just copy it over.
        eq_(obj.trans_desc, u'This is English.')

    @override_settings(
        ADMINS=(('Jimmy Discotheque', 'jimmy@example.com'),),
        GENGO_ACCOUNT_BALANCE_THRESHOLD=20.0
    )
    @account_balance(0.0)
    def test_push_translations_low_balance_mails_admin(self):
        """Tests that a low balance sends email and does nothing else"""
        # Verify nothing is in the outbox
        eq_(len(mail.outbox), 0)

        # Call push_translation which should balk and email the
        # admin
        ght = GengoHumanTranslator()
        ght.push_translations()

        # Verify an email got sent and no jobs were created
        eq_(len(mail.outbox), 1)
        eq_(GengoJob.objects.count(), 0)

    @override_settings(GENGO_ACCOUNT_BALANCE_THRESHOLD=20.0)
    def test_gengo_push_translations(self):
        """Tests GengoOrders get created"""
        ght = GengoHumanTranslator()

        # Create a few jobs covering multiple languages
        descs = [
            ('es', u'Facebook no se puede enlazar con peru'),
            ('es', u'No es compatible con whatsap'),

            ('de', u'Absturze und langsam unter Android'),
        ]
        for lang, desc in descs:
            obj = SuperModel(locale=lang, desc=desc)
            obj.save()

            job = GengoJob(
                content_object=obj,
                src_field='desc',
                dst_field='trans_desc',
                src_lang=lang,
                dst_lang='en'
            )
            job.save()

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            # FIXME: This returns the same thing both times, but to
            # make the test "more kosher" we'd have this return two
            # different order_id values.
            mocker = GengoMock.return_value
            mocker.getAccountBalance.return_value = {
                u'opstat': u'ok',
                u'response': {
                    u'credits': '400.00',
                    u'currency': u'USD'
                }
            }
            mocker.postTranslationJobs.return_value = {
                u'opstat': u'ok',
                u'response': {
                    u'order_id': u'1337',
                    u'job_count': 2,
                    u'credits_used': u'0.35',
                    u'currency': u'USD'
                }
            }

            ght.push_translations()

            eq_(GengoOrder.objects.count(), 2)

            order_by_id = dict(
                [(order.id, order) for order in GengoOrder.objects.all()]
            )

            jobs = GengoJob.objects.all()
            for job in jobs:
                assert job.order_id in order_by_id

    @override_settings(
        ADMINS=(('Jimmy Discotheque', 'jimmy@example.com'),),
        GENGO_ACCOUNT_BALANCE_THRESHOLD=20.0
    )
    def test_gengo_push_translations_not_enough_balance(self):
        """Tests enough balance for one order, but not both"""
        ght = GengoHumanTranslator()

        # Create a few jobs covering multiple languages
        descs = [
            ('es', u'Facebook no se puede enlazar con peru'),
            ('de', u'Absturze und langsam unter Android'),
        ]
        for lang, desc in descs:
            obj = SuperModel(locale=lang, desc=desc)
            obj.save()

            job = GengoJob(
                content_object=obj,
                src_field='desc',
                dst_field='trans_desc',
                src_lang=lang,
                dst_lang='en'
            )
            job.save()

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            # FIXME: This returns the same thing both times, but to
            # make the test "more kosher" we'd have this return two
            # different order_id values.
            mocker = GengoMock.return_value
            mocker.getAccountBalance.return_value = {
                u'opstat': u'ok',
                u'response': {
                    # Enough for one order, but dips below threshold
                    # for the second one.
                    u'credits': '20.30',
                    u'currency': u'USD'
                }
            }
            mocker.postTranslationJobs.return_value = {
                u'opstat': u'ok',
                u'response': {
                    u'order_id': u'1337',
                    u'job_count': 2,
                    u'credits_used': u'0.35',
                    u'currency': u'USD'
                }
            }

            ght.push_translations()

            eq_(GengoOrder.objects.count(), 1)
            eq_(len(mail.outbox), 1)

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            # FIXME: This returns the same thing both times, but to
            # make the test "more kosher" we'd have this return two
            # different order_id values.
            mocker = GengoMock.return_value
            mocker.getAccountBalance.return_value = {
                u'opstat': u'ok',
                u'response': {
                    # This is the balance after one order.
                    u'credits': '19.95',
                    u'currency': u'USD'
                }
            }
            mocker.postTranslationJobs.return_value = {
                u'opstat': u'ok',
                u'response': {
                    u'order_id': u'1337',
                    u'job_count': 2,
                    u'credits_used': u'0.35',
                    u'currency': u'USD'
                }
            }

            # The next time push_translations runs, it shouldn't
            # create any new jobs, but should send an email.
            ght.push_translations()

            eq_(GengoOrder.objects.count(), 1)
            eq_(len(mail.outbox), 2)


def use_sandbox(fun):
    """Decorator to force the use of the sandbox

    This forces the test to use ths Gengo sandbox. This requires that
    you have GENGO_SANDBOX_PUBLIC_KEY and GENGO_SANDBOX_PRIVATE_KEY
    set up. If you don't, then they're made blank and the tests will
    fail and we will all freeze in an ice storm of biblical
    proportions!

    """
    public_key = getattr(settings, 'GENGO_SANDBOX_PUBLIC_KEY', '')
    private_key = getattr(settings, 'GENGO_SANDBOX_PRIVATE_KEY', '')

    return override_settings(
        GENGO_PUBLIC_KEY=public_key,
        GENGO_PRIVATE_KEY=private_key,
        GENGO_USE_SANDBOX=True
    )(fun)


@skip_if(lambda: not has_gengo_creds())
class LiveGengoTestCase(TestCase):
    """These are tests that execute calls against the real live Gengo API

    These tests require GENGO_PUBLIC_KEY and GENGO_PRIVATE_KEY to be
    valid values in your settings_local.py file.

    These tests will use the sandbox where possible, but otherwise use
    the real live Gengo API.

    Please don't fake the credentials since then you'll just get API
    authentication errors.

    These tests should be minimal end-to-end tests.

    """
    def setUp(self):
        # Wipe out the GENGO_LANGUAGE_CACHE
        gengo_utils.GENGO_LANGUAGE_CACHE = None
        super(LiveGengoTestCase, self).setUp()

    def test_get_language(self):
        text = u'Facebook no se puede enlazar con peru'
        gengo_api = gengo_utils.FjordGengo()
        eq_(gengo_api.guess_language(text), u'es')

    @skip_if(lambda: getattr(settings, 'GENGO_USE_SANDBOX', True))
    def test_gengo_machine_translation(self):
        # Note: This doesn't work in the sandbox, so we skip it if
        # we're in sandbox mode. That is some happy horseshit, but so
        # it goes.

        # Note: This test might be brittle since it's calling out to
        # Gengo to do a machine translation and it's entirely possible
        # that they might return a different translation some day.
        obj = SuperModel(
            locale='es',
            desc=u'Facebook no se puede enlazar con peru'
        )
        obj.save()

        eq_(obj.trans_desc, u'')
        translate(obj, 'gengo_machine', 'es', 'desc', 'en', 'trans_desc')
        eq_(obj.trans_desc, u'Facebook can bind with peru')
