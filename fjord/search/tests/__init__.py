from django.conf import settings

import pyes.urllib3
import pyes.exceptions
from nose import SkipTest
from test_utils import TestCase

from fjord.search.models import get_index
from fjord.search.utils import get_indexing_es


class ElasticTestCase(TestCase):
    """Base class for Elastic Search tests, providing some conveniences"""
    skipme = False

    @classmethod
    def setUpClass(cls):
        super(ElasticTestCase, cls).setUpClass()

        if not getattr(settings, 'ES_HOSTS'):
            cls.skipme = True
            return

        # try to connect to ES and if it fails, skip ElasticTestCases.
        try:
            get_indexing_es().collect_info()
        except pyes.urllib3.MaxRetryError:
            cls.skipme = True
            return

        cls._old_es_index_prefix = settings.ES_INDEX_PREFIX
        settings.ES_INDEX_PREFIX = settings.ES_INDEX_PREFIX + 'test'

    @classmethod
    def tearDownClass(cls):
        super(ElasticTestCase, cls).tearDownClass()
        if not cls.skipme:
            # Restore old setting.
            settings.ES_INDEX_PREFIX = cls._old_es_index_prefix

    def setUp(self):
        if self.skipme:
            raise SkipTest

        super(ElasticTestCase, self).setUp()
        self.setup_indexes()
        self.refresh(settings.ES_TEST_SLEEP_DURATION)

    def tearDown(self):
        super(ElasticTestCase, self).tearDown()
        self.teardown_indexes()

    def refresh(self, timesleep=0):
        index = get_index()

        # Any time we're doing a refresh, we're making sure that the
        # index is ready to be queried.  Given that, it's almost
        # always the case that we want to run all the generated tasks,
        # then refresh.
        # TODO: uncomment this when we have live indexing.
        # generate_tasks()

        get_indexing_es().refresh(index, timesleep=timesleep)

    def setup_indexes(self):
        """(Re-)create ES indexes."""
        from fjord.search.utils import es_reindex_cmd

        # This removes the previous round of indexes and creates new
        # ones with mappings and all that.
        es_reindex_cmd()

    def teardown_indexes(self):
        es = get_indexing_es()
        es.delete_index_if_exists(get_index())
