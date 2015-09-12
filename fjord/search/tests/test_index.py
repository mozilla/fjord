from fjord.feedback.models import ResponseDocType
from fjord.feedback.tests import ResponseFactory
from fjord.search.index import chunked
from fjord.search.tests import ElasticTestCase


def test_chunked():
    # chunking nothing yields nothing.
    assert list(chunked([], 1)) == []

    # chunking list where len(list) < n
    assert list(chunked([1], 10)) == [(1,)]

    # chunking a list where len(list) == n
    assert list(chunked([1, 2], 2)) == [(1, 2)]

    # chunking list where len(list) > n
    assert list(chunked([1, 2, 3, 4, 5], 2)) == [(1, 2), (3, 4), (5,)]


class TestLiveIndexing(ElasticTestCase):
    def test_live_indexing(self):
        search = ResponseDocType.docs.search()
        count_pre = search.count()

        s = ResponseFactory(happy=True, description='Test live indexing.')
        self.refresh()
        assert count_pre + 1 == search.count()

        s.delete()
        self.refresh()
        assert count_pre == search.count()
