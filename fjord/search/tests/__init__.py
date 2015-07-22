import time

from django.conf import settings

import factory
from elasticsearch.exceptions import NotFoundError

from fjord.base.tests import BaseTestCase
from fjord.search.index import (
    es_reindex_cmd,
    get_index_name,
    get_es,
    recreate_index
)
from fjord.search.models import Record


class ElasticTestCase(BaseTestCase):
    """Base class for Elastic Search tests, providing some conveniences"""
    @classmethod
    def setUpClass(cls):
        super(ElasticTestCase, cls).setUpClass()

        cls._old_es_index_prefix = settings.ES_INDEX_PREFIX
        settings.ES_INDEX_PREFIX = settings.ES_INDEX_PREFIX + 'test'

    @classmethod
    def tearDownClass(cls):
        super(ElasticTestCase, cls).tearDownClass()

        # Restore old setting.
        settings.ES_INDEX_PREFIX = cls._old_es_index_prefix

    def setUp(self):
        super(ElasticTestCase, self).setUp()
        self.setup_indexes()

    def tearDown(self):
        super(ElasticTestCase, self).tearDown()
        self.teardown_indexes()

    def refresh(self, timesleep=0):
        get_es().indices.refresh()
        if timesleep > 0:
            time.sleep(timesleep)

    def setup_indexes(self, empty=False, wait=True):
        """(Re-)create ES indexes."""
        if empty:
            recreate_index()
        else:
            # Removes the index, creates a new one, and indexes
            # existing data into it.
            es_reindex_cmd()

        self.refresh()
        if wait:
            get_es().cluster.health(wait_for_status='yellow')

    def teardown_indexes(self):
        try:
            get_es().indices.delete(get_index_name())
        except NotFoundError:
            # If we get this error, it means the index didn't exist
            # so there's nothing to delete.
            pass


class RecordFactory(factory.DjangoModelFactory):
    class Meta:
        model = Record

    batch_id = 'ou812'
    name = 'Frank'
