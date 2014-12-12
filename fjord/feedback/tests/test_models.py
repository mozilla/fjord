import datetime

from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.feedback.models import (
    Product,
    Response,
    ResponseEmail,
    ResponseContext,
    ResponseMappingType,
    purge_data
)
from fjord.feedback.tests import (
    ResponseFactory,
    ResponseEmailFactory,
    ResponseContextFactory
)
from fjord.feedback.utils import compute_grams
from fjord.search.tests import ElasticTestCase
from fjord.feedback.config import TRUNCATE_LENGTH


class TestResponseModel(TestCase):
    def test_description_truncate_on_save(self):
        # Extra 10 characters get lopped off on save.
        resp = ResponseFactory(description=('a' * (TRUNCATE_LENGTH + 10)))
        eq_(resp.description, 'a' * TRUNCATE_LENGTH)

    def test_description_strip_on_save(self):
        # Nix leading and trailing whitespace.
        resp = ResponseFactory(description=u'   \n\tou812\t\n   ')
        eq_(resp.description, u'ou812')

    def test_url_domain(self):
        # Test a "normal domain"
        resp = ResponseFactory(url=u'http://foo.example.com.br/blah')
        eq_(resp.url_domain, u'example.com.br')
        assert isinstance(resp.url_domain, unicode)

        # Test a unicode domain
        resp = ResponseFactory(
            url=u'http://\u30c9\u30e9\u30af\u30a810.jp/dq10_skillpoint.html')
        eq_(resp.url_domain, u'\u30c9\u30e9\u30af\u30a810.jp')
        assert isinstance(resp.url_domain, unicode)

    def test_rating_to_happy(self):
        """Test that we do populate happy from rating"""
        data = {
            1: False,
            2: False,
            3: False,
            4: True,
            5: True
        }
        for rat, expected in data.items():
            # Create the response, but DON'T save it to the db.
            resp = ResponseFactory.build(happy=None, rating=rat)
            resp.save()
            eq_(resp.happy, expected)

    def test_happy_to_rating(self):
        """Test we don't populate rating from happy"""
        resp = ResponseFactory.build(happy=True, rating=None)
        resp.save()
        eq_(resp.rating, None)

        resp = ResponseFactory.build(happy=False, rating=None)
        resp.save()
        eq_(resp.rating, None)


class TestAutoTranslation(TestCase):
    def setUp(self):
        # Wipe out translation system for all products.

        # FIXME - might be better to save the state and restore it in tearDown
        # rather than stomp in both cases. But stomping works for now.
        Product.objects.update(translation_system=u'')
        super(TestAutoTranslation, self).setUp()

    def tearDown(self):
        # Wipe out translation system for all products.
        Product.objects.update(translation_system=u'')
        super(TestAutoTranslation, self).tearDown()

    def test_auto_translation(self):
        prod = Product.uncached.get(db_name='firefox')
        prod.translation_system = u'dennis'
        prod.save()

        resp = ResponseFactory(
            locale=u'es',
            product=u'firefox',
            description=u'hola'
        )

        # Fetch it from the db again
        resp = Response.uncached.get(id=resp.id)
        eq_(resp.translated_description, u'\xabHOLA\xbb')


class TestGenerateTranslationJobs(TestCase):
    def setUp(self):
        # Wipe out translation system for all products.

        # FIXME - might be better to save the state and restore it in tearDown
        # rather than stomp in both cases. But stomping works for now.
        Product.objects.update(translation_system=u'')
        super(TestGenerateTranslationJobs, self).setUp()

    def tearDown(self):
        # Wipe out translation system for all products.
        Product.objects.update(translation_system=u'')
        super(TestGenerateTranslationJobs, self).tearDown()

    def test_english_no_translation(self):
        """English descriptions should get copied over"""
        resp = ResponseFactory(
            locale=u'en-US',
            description=u'hello',
            translated_description=u''
        )

        # No new jobs should be generated
        eq_(len(resp.generate_translation_jobs()), 0)

        # Re-fetch from the db and make sure the description was copied over
        resp = Response.uncached.get(id=resp.id)
        eq_(resp.description, resp.translated_description)

    def test_english_gb_no_translation(self):
        """en-GB descriptions should get copied over"""
        resp = ResponseFactory(
            locale=u'en-GB',
            description=u'hello',
            translated_description=u''
        )

        # No new jobs should be generated
        eq_(len(resp.generate_translation_jobs()), 0)

        # Re-fetch from the db and make sure the description was copied over
        resp = Response.uncached.get(id=resp.id)
        eq_(resp.description, resp.translated_description)

    def test_english_with_dennis(self):
        """English descriptions should get copied over"""
        resp = ResponseFactory(
            locale=u'en-US',
            product=u'firefox',
            description=u'hello',
            translated_description=u''
        )

        # Set the product up for translation *after* creating the response
        # so that it doesn't get auto-translated because Response is set up
        # for auto-translation.
        prod = Product.uncached.get(db_name='firefox')
        prod.translation_system = u'dennis'
        prod.save()

        # No new jobs should be generated
        eq_(len(resp.generate_translation_jobs()), 0)

        # Re-fetch from the db and make sure the description was copied over
        resp = Response.uncached.get(id=resp.id)
        eq_(resp.description, resp.translated_description)

    def test_spanish_no_translation(self):
        """Spanish should not get translated"""
        resp = ResponseFactory(
            locale=u'es',
            product=u'firefox',
            description=u'hola',
            translated_description=u''
        )

        # No jobs should be translated
        eq_(len(resp.generate_translation_jobs()), 0)

        # Nothing should be translated
        eq_(resp.translated_description, u'')

    def test_spanish_with_dennis(self):
        """Spanish should get translated"""
        resp = ResponseFactory(
            locale=u'es',
            product=u'firefox',
            description=u'hola',
            translated_description=u''
        )

        # Set the product up for translation *after* creating the response
        # so that it doesn't get auto-translated because Response is set up
        # for auto-translation.
        prod = Product.uncached.get(db_name='firefox')
        prod.translation_system = u'dennis'
        prod.save()

        # One job should be generated
        jobs = resp.generate_translation_jobs()
        eq_(len(jobs), 1)
        job = jobs[0]
        eq_(job[1:], (u'dennis', u'es', u'description',
                      u'en', 'translated_description'))

        eq_(resp.translated_description, u'')

    def test_spanish_with_dennis_and_existing_translations(self):
        """Response should pick up existing translation"""
        existing_resp = ResponseFactory(
            locale=u'es',
            product=u'firefox',
            description=u'hola',
            translated_description=u'DUDE!'
        )

        resp = ResponseFactory(
            locale=u'es',
            product=u'firefox',
            description=u'hola',
            translated_description=u''
        )

        # Set the product up for translation *after* creating the response
        # so that it doesn't get auto-translated because Response is set up
        # for auto-translation.
        prod = Product.uncached.get(db_name='firefox')
        prod.translation_system = u'dennis'
        prod.save()

        # No jobs should be translated
        eq_(len(resp.generate_translation_jobs()), 0)
        eq_(resp.translated_description, existing_resp.translated_description)


class TestComputeGrams(TestCase):
    def test_empty(self):
        eq_(compute_grams(u''), [])

    def test_parsing(self):
        # stop words are removed
        eq_(compute_grams(u'i me him her'), [])

        # capital letters don't matter
        eq_(compute_grams(u'I ME HIM HER'), [])

        # punctuation nixed
        eq_(compute_grams(u'i, me, him, her'), [])

    def test_bigrams(self):
        # Note: Tokens look weird after being analyzed probably due to
        # the stemmer. We could write a bunch of code to "undo" some
        # of the excessive stemming, but it's probably an exercise in
        # futility. Ergo the tests look a little odd. e.g. "youtub"

        # One word a bigram does not make
        eq_(compute_grams(u'youtube'), [])

        # Two words is the minimum number to create a bigram
        eq_(sorted(compute_grams(u'youtube crash')),
            ['crash youtube'])

        # Three words creates two bigrams
        eq_(sorted(compute_grams(u'youtube crash flash')),
            ['crash flash', 'crash youtube'])

        # Four words creates three bigrams
        eq_(sorted(compute_grams(u'youtube crash flash bridge')),
            ['bridge flash', 'crash flash', 'crash youtube'])

        # Nix duplicate bigrams
        eq_(sorted(compute_grams(u'youtube crash youtube flash')),
            ['crash youtube', 'flash youtube'])


class TestParseData(ElasticTestCase):
    def test_purge(self):
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(days=5)

        # Create 10 ResponseEmail objs--one for each day for the last
        # 10 days.
        for i in range(10):
            ResponseEmailFactory(
                opinion__created=(now - datetime.timedelta(days=i))
            )
            ResponseContextFactory(
                opinion__created=(now - datetime.timedelta(days=i))
            )

        # Since creating the objects and indexing them happens very
        # quickly in tests, we hit a race condition and the has_email
        # column ends up being false. So instead we just drop the
        # index and rebuild it.
        self.setup_indexes()

        # Make sure everything is in the db
        eq_(Response.objects.count(), 20)
        eq_(ResponseEmail.objects.count(), 10)
        eq_(ResponseContext.objects.count(), 10)

        # Make sure everything is in the index
        resp_s = ResponseMappingType.search()
        eq_(resp_s.count(), 20)
        eq_(resp_s.filter(has_email=True).count(), 10)

        # Now purge everything older than 5 days and make sure things
        # got removed that should have gotten removed
        cutoff = now - datetime.timedelta(days=5)
        purge_data(cutoff=cutoff)

        self.refresh()

        eq_(Response.objects.count(), 20)
        eq_(ResponseEmail.objects.count(), 5)
        eq_(ResponseEmail.objects.filter(
            opinion__created__gte=cutoff).count(),
            5)
        eq_(ResponseContext.objects.count(), 5)
        eq_(ResponseContext.objects.filter(
            opinion__created__gte=cutoff).count(),
            5)

        # Everything should still be in the index, but the number of
        # things with has_email=True should go down
        resp_s = ResponseMappingType.search()
        eq_(resp_s.count(), 20)
        eq_(resp_s.filter(has_email=True).count(), 5)
