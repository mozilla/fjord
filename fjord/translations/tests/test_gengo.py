from functools import wraps

from django.core import mail
from django.test.utils import override_settings

from mock import MagicMock, patch
import requests_mock
import pytest

from fjord.base.tests import TestCase
from fjord.translations import gengo_utils
from fjord.translations.models import (
    GengoHumanTranslator,
    GengoMachineTranslator,
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
        gengo_utils.GENGO_LANGUAGE_PAIRS_CACHE = [
            (u'es', u'en'), (u'en', u'es-la'), (u'de', u'pl')
        ]

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
            elif lang == 'el':
                ret.update({
                    u'detected_lang_code': u'el',
                    u'details': [
                        [u'GREEK', u'el', 62, 46.728971962616825],
                        [u'ITALIAN', u'it', 38, 9.237875288683602]
                    ],
                    u'detected_lang_name': u'GREEK'
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

            with requests_mock.Mocker() as m:
                m.post(gengo_utils.GENGO_DETECT_LANGUAGE_API, json=ret)
                return fun(*args, **kwargs)

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
        assert gengo_api.guess_language(text) == u'es'

    def test_guess_language_unintelligible_response(self):
        # If the gengo api returns some crazy non-json response, make sure
        # that guess_language should throw a GengoAPIFailure.
        gengo_api = gengo_utils.FjordGengo()

        with patch('fjord.translations.gengo_utils.requests') as req_patch:
            # Create a mock that we can call .post() on and it returns
            # a response that has a .json() method that throws a
            # ValueError which is what happens when it's not valid
            # JSON.
            post_return = MagicMock()
            post_return.text = 'abcd'
            post_return.status_code = 500
            post_return.json.side_effect = ValueError('bleh')
            req_patch.post.return_value = post_return

            self.assertRaises(
                gengo_utils.GengoAPIFailure,
                gengo_api.guess_language,
                u'whatever text'
            )


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
            instance = GengoMock.return_value
            instance.getServiceLanguages.return_value = response

            # Make sure the cache is empty
            assert gengo_utils.GENGO_LANGUAGE_CACHE == None

            # Test that we generate a list based on what we think the
            # response is.
            gengo_api = gengo_utils.FjordGengo()
            assert gengo_api.get_languages() == (u'es',)

            # Test that the new list is cached.
            assert gengo_utils.GENGO_LANGUAGE_CACHE == (response, (u'es',))


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class GetLanguagePairsTestCase(BaseGengoTestCase):
    def test_get_language_pairs(self):
        resp = {
            u'opstat': u'ok',
            u'response': [
                {u'tier': u'standard', u'lc_tgt': u'es-la', u'lc_src': u'en',
                 u'unit_price': u'0.05', u'currency': u'USD'},
                {u'tier': u'ultra', u'lc_tgt': u'ar', u'lc_src': u'en',
                 u'unit_price': u'0.15', u'currency': u'USD'},
                {u'tier': u'pro', u'lc_tgt': u'ar', u'lc_src': u'en',
                 u'unit_price': u'0.10', u'currency': u'USD'},
                {u'tier': u'ultra', u'lc_tgt': u'es', u'lc_src': u'en',
                 u'unit_price': u'0.15', u'currency': u'USD'},
                {u'tier': u'standard', u'lc_tgt': u'pl', u'lc_src': u'de',
                 u'unit_price': u'0.05', u'currency': u'USD'}
            ]
        }

        gengo_utils.GENGO_LANGUAGE_PAIRS_CACHE = None

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            instance = GengoMock.return_value
            instance.getServiceLanguagePairs.return_value = resp

            # Make sure the cache is empty
            assert gengo_utils.GENGO_LANGUAGE_PAIRS_CACHE == None

            # Test that we generate a list based on what we think the
            # response is.
            gengo_api = gengo_utils.FjordGengo()
            assert (
                gengo_api.get_language_pairs() ==
                [(u'en', u'es-la'), (u'de', u'pl')]
                )

            # Test that the new list is cached.
            assert (
                gengo_utils.GENGO_LANGUAGE_PAIRS_CACHE ==
                [(u'en', u'es-la'), (u'de', u'pl')]
                )


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class GetBalanceTestCase(BaseGengoTestCase):
    @account_balance(20.0)
    def test_get_balance(self):
        gengo_api = gengo_utils.FjordGengo()
        assert gengo_api.get_balance() == 20.0


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class MachineTranslateTestCase(BaseGengoTestCase):
    @guess_language('es')
    def test_translate_gengo_machine(self):
        # Note: This just sets up the GengoJob--it doesn't create any
        # Gengo human translation jobs.
        obj = SuperModel(
            locale='es',
            desc=u'Facebook no se puede enlazar con peru'
        )
        obj.save()

        assert obj.trans_desc == u''
        translate(obj, 'gengo_machine', 'es', 'desc', 'en', 'trans_desc')
        # Nothing should be translated
        assert obj.trans_desc == u''

        assert len(GengoJob.objects.all()) == 1

    def test_gengo_push_translations(self):
        """Tests GengoOrders get created"""
        ght = GengoMachineTranslator()

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
                tier='machine',
                src_field='desc',
                dst_field='trans_desc',
                src_lang=lang,
                dst_lang='en'
            )
            job.save()

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            mocker = GengoMock.return_value

            # FIXME: This returns the same thing both times, but to
            # make the test "more kosher" we'd have this return two
            # different order_id values.
            mocker.postTranslationJobs.return_value = {
                u'opstat': u'ok',
                u'response': {
                    u'order_id': u'1337',
                    u'job_count': 2,
                    u'credits_used': u'0.0',
                    u'currency': u'USD'
                }
            }

            ght.push_translations()

            assert GengoOrder.objects.count() == 2

            order_by_id = dict(
                [(order.id, order) for order in GengoOrder.objects.all()]
            )

            jobs = GengoJob.objects.all()
            for job in jobs:
                assert job.order_id in order_by_id


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

        assert obj.trans_desc == u''
        translate(obj, 'gengo_human', 'es', 'desc', 'en', 'trans_desc')
        # Nothing should be translated
        assert obj.trans_desc == u''

        assert len(GengoJob.objects.all()) == 1

    @guess_language('es')
    def test_no_translate_if_disabled(self):
        """No GengoAPI calls if gengosystem switch is disabled"""
        with patch('fjord.translations.models.waffle') as waffle_mock:
            waffle_mock.switch_is_active.return_value = False

            with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
                # Note: This just sets up the GengoJob--it doesn't
                # create any Gengo human translation jobs.
                obj = SuperModel(
                    locale='es',
                    desc=u'Facebook no se puede enlazar con peru'
                )
                obj.save()

                assert obj.trans_desc == u''
                translate(obj, 'gengo_human', 'es', 'desc', 'en', 'trans_desc')
                assert obj.trans_desc == u''

                # Verify no jobs were created
                assert len(GengoJob.objects.all()) == 0

                # Verify we didn't call the API at all.
                assert GengoMock.called == False

    @guess_language('en')
    def test_translate_gengo_human_english_copy_over(self):
        obj = SuperModel(
            locale='es',
            desc=u'This is English.'
        )
        obj.save()

        assert obj.trans_desc == u''
        translate(obj, 'gengo_human', 'es', 'desc', 'en', 'trans_desc')
        # If the guesser guesses English, then we just copy it over.
        assert obj.trans_desc == u'This is English.'

    @guess_language('el')
    def test_translate_gengo_human_unsupported_pair(self):
        obj = SuperModel(
            locale='el',
            desc=u'This is really greek.'
        )
        obj.save()

        assert obj.trans_desc == u''
        translate(obj, 'gengo_human', 'el', 'desc', 'en', 'trans_desc')
        # el -> en is not a supported pair, so it shouldn't get translated.
        assert obj.trans_desc == u''

    @override_settings(
        ADMINS=(('Jimmy Discotheque', 'jimmy@example.com'),),
        GENGO_ACCOUNT_BALANCE_THRESHOLD=20.0
    )
    @account_balance(0.0)
    def test_push_translations_low_balance_mails_admin(self):
        """Tests that a low balance sends email and does nothing else"""
        # Verify nothing is in the outbox
        assert len(mail.outbox) == 0

        # Call push_translation which should balk and email the
        # admin
        ght = GengoHumanTranslator()
        ght.push_translations()

        # Verify an email got sent and no jobs were created
        assert len(mail.outbox) == 1
        assert GengoJob.objects.count() == 0

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
                tier='standard',
                src_field='desc',
                dst_field='trans_desc',
                src_lang=lang,
                dst_lang='en'
            )
            job.save()

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            mocker = GengoMock.return_value
            mocker.getAccountBalance.return_value = {
                u'opstat': u'ok',
                u'response': {
                    u'credits': '400.00',
                    u'currency': u'USD'
                }
            }
            # FIXME: This returns the same thing both times, but to
            # make the test "more kosher" we'd have this return two
            # different order_id values.
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

            assert GengoOrder.objects.count() == 2

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
                tier='standard',
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

            assert GengoOrder.objects.count() == 1
            # The "it's too low" email only.
            assert len(mail.outbox) == 1

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

            assert GengoOrder.objects.count() == 1
            # This generates one more email.
            assert len(mail.outbox) == 2

    @override_settings(
        ADMINS=(('Jimmy Discotheque', 'jimmy@example.com'),),
        GENGO_ACCOUNT_BALANCE_THRESHOLD=20.0
    )
    def test_gengo_daily_activities_warning(self):
        """Tests warning email is sent"""
        ght = GengoHumanTranslator()

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
                    u'credits': '30.00',
                    u'currency': u'USD'
                }
            }

            ght.run_daily_activities()

            # The "balance is low warning" email only.
            assert len(mail.outbox) == 1


@override_settings(GENGO_PUBLIC_KEY='ou812', GENGO_PRIVATE_KEY='ou812')
class CompletedJobsForOrderTestCase(BaseGengoTestCase):
    def test_no_approved_jobs(self):
        gtoj_resp = {
            u'opstat': u'ok',
            u'response': {
                u'order': {
                    u'jobs_pending': [u'746197'],
                    u'jobs_revising': [],
                    u'as_group': 0,
                    u'order_id': u'263413',
                    u'jobs_queued': u'0',
                    u'total_credits': u'0.35',
                    u'currency': u'USD',
                    u'total_units': u'7',
                    u'jobs_approved': [],
                    u'jobs_reviewable': [],
                    u'jobs_available': [],
                    u'total_jobs': u'1'
                }
            }
        }

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            instance = GengoMock.return_value
            instance.getTranslationOrderJobs.return_value = gtoj_resp

            gengo_api = gengo_utils.FjordGengo()
            jobs = gengo_api.completed_jobs_for_order('263413')
            assert jobs == []

    def test_approved_jobs(self):
        gtoj_resp = {
            u'opstat': u'ok',
            u'response': {
                u'order': {
                    u'jobs_pending': [],
                    u'jobs_revising': [],
                    u'as_group': 0,
                    u'order_id': u'263413',
                    u'jobs_queued': u'0',
                    u'total_credits': u'0.35',
                    u'currency': u'USD',
                    u'total_units': u'7',
                    u'jobs_approved': [u'746197'],
                    u'jobs_reviewable': [],
                    u'jobs_available': [],
                    u'total_jobs': u'1'
                }
            }
        }

        gtjb_resp = {
            u'opstat': u'ok',
            u'response': {
                u'jobs': [
                    {
                        u'status': u'approved',
                        u'job_id': u'746197',
                        u'currency': u'USD',
                        u'order_id': u'263413',
                        u'body_tgt': u'Facebook can bind with peru',
                        u'body_src': u'Facebook no se puede enlazar con peru',
                        u'credits': u'0.35',
                        u'eta': -1,
                        u'custom_data': u'localhost||GengoJob||7',
                        u'tier': u'standard',
                        u'lc_tgt': u'en',
                        u'lc_src': u'es',
                        u'auto_approve': u'1',
                        u'unit_count': u'7',
                        u'slug': u'Mozilla Input feedback response',
                        u'ctime': 1403296006
                    }
                ]
            }
        }

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            instance = GengoMock.return_value
            instance.getTranslationOrderJobs.return_value = gtoj_resp
            instance.getTranslationJobBatch.return_value = gtjb_resp

            gengo_api = gengo_utils.FjordGengo()
            jobs = gengo_api.completed_jobs_for_order('263413')
            assert(
                [item['custom_data'] for item in jobs] ==
                [u'localhost||GengoJob||7']
                )

    def test_pull_translations(self):
        ght = GengoHumanTranslator()

        obj = SuperModel(locale='es', desc=u'No es compatible con whatsap')
        obj.save()

        gj = GengoJob(
            content_object=obj,
            tier='standard',
            src_field='desc',
            dst_field='trans_desc',
            src_lang='es',
            dst_lang='en'
        )
        gj.save()

        order = GengoOrder(order_id=u'263413')
        order.save()

        gj.assign_to_order(order)

        gtoj_resp = {
            u'opstat': u'ok',
            u'response': {
                u'order': {
                    u'jobs_pending': [],
                    u'jobs_revising': [],
                    u'as_group': 0,
                    u'order_id': u'263413',
                    u'jobs_queued': u'0',
                    u'total_credits': u'0.35',
                    u'currency': u'USD',
                    u'total_units': u'7',
                    u'jobs_approved': [u'746197'],
                    u'jobs_reviewable': [],
                    u'jobs_available': [],
                    u'total_jobs': u'1'
                }
            }
        }

        gtjb_resp = {
            u'opstat': u'ok',
            u'response': {
                u'jobs': [
                    {
                        u'status': u'approved',
                        u'job_id': u'746197',
                        u'currency': u'USD',
                        u'order_id': u'263413',
                        u'body_tgt': u'No es compatible con whatsap',
                        u'body_src': u'Not compatible with whatsap',
                        u'credits': u'0.35',
                        u'eta': -1,
                        u'custom_data': u'localhost||GengoJob||{0}'.format(
                            gj.id),
                        u'tier': u'standard',
                        u'lc_tgt': u'en',
                        u'lc_src': u'es',
                        u'auto_approve': u'1',
                        u'unit_count': u'7',
                        u'slug': u'Mozilla Input feedback response',
                        u'ctime': 1403296006
                    }
                ]
            }
        }

        with patch('fjord.translations.gengo_utils.Gengo') as GengoMock:
            instance = GengoMock.return_value
            instance.getTranslationOrderJobs.return_value = gtoj_resp
            instance.getTranslationJobBatch.return_value = gtjb_resp

            ght.pull_translations()

            jobs = GengoJob.objects.all()
            assert len(jobs) == 1
            assert jobs[0].status == 'complete'

            orders = GengoOrder.objects.all()
            assert len(orders) == 1
            assert orders[0].status == 'complete'


@pytest.mark.skipif(not has_gengo_creds(),
                    reason='no gengo creds')
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
        # Wipe out the caches
        gengo_utils.GENGO_LANGUAGE_CACHE = None
        gengo_utils.GENGO_LANGUAGE_PAIRS_CACHE = None
        super(LiveGengoTestCase, self).setUp()

    def test_get_language(self):
        text = u'Facebook no se puede enlazar con peru'
        gengo_api = gengo_utils.FjordGengo()
        assert gengo_api.guess_language(text) == u'es'
