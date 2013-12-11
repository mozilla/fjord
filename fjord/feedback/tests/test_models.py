from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.feedback.tests import response
from fjord.feedback.utils import compute_grams
from fjord.search.tests import ElasticTestCase


class TestResponseModel(TestCase):
    def test_description_truncate_on_save(self):
        # Extra 10 characters get lopped off on save.
        resp = response(description=('a' * 10010))
        resp.save()

        eq_(resp.description, 'a' * 10000)

    def test_description_strip_on_save(self):
        # Nix leading and trailing whitespace.
        resp = response(description=u'   \n\tou812\t\n   ')
        resp.save()

        eq_(resp.description, u'ou812')


class TestComputeGrams(ElasticTestCase):
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
            ['crash youtub'])

        # Three words creates two bigrams
        eq_(sorted(compute_grams(u'youtube crash flash')),
            ['crash flash', 'crash youtub'])

        # Four words creates three bigrams
        eq_(sorted(compute_grams(u'youtube crash flash bridge')),
            ['bridg flash', 'crash flash', 'crash youtub'])

        # Nix duplicate bigrams
        eq_(sorted(compute_grams(u'youtube crash youtube flash')),
            ['crash youtub', 'flash youtub'])
