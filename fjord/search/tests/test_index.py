from nose.tools import eq_
from test_utils import TestCase

from fjord.feedback.models import SimpleIndex
from fjord.feedback.tests import simple
from fjord.search.index import chunked
from fjord.search.tests import ElasticTestCase


class ChunkedTests(TestCase):
    def test_chunked(self):
        # chunking nothing yields nothing.
        eq_(list(chunked([], 1)), [])

        # chunking list where len(list) < n
        eq_(list(chunked([1], 10)), [(1,)])

        # chunking a list where len(list) == n
        eq_(list(chunked([1, 2], 2)), [(1, 2)])

        # chunking list where len(list) > n
        eq_(list(chunked([1, 2, 3, 4, 5], 2)),
            [(1, 2), (3, 4), (5,)])


class TestLiveIndexing(ElasticTestCase):

    def test_live_indexing(self):
        S = SimpleIndex.search
        count_pre = S().count()

        s = simple(happy=True, description='Test live indexing.', save=True)
        self.refresh()
        eq_(count_pre + 1, S().count())

        s.delete()
        self.refresh()
        eq_(count_pre, S().count())
