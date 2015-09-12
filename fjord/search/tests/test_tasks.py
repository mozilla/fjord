from fjord.feedback.models import ResponseDocType
from fjord.feedback.tests import ResponseFactory
from fjord.search.index import get_index_name
from fjord.search.models import Record
from fjord.search.tasks import index_chunk_task
from fjord.search.tests import RecordFactory, ElasticTestCase
from fjord.search.utils import to_class_path


class TestIndexChunkTask(ElasticTestCase):
    def test_index_chunk_task(self):
        responses = ResponseFactory.create_batch(10)

        # With live indexing, that'll create items in the index. Since
        # we want to test index_chunk_test, we need a clean index to
        # start with so we delete and recreate it.
        self.setup_indexes(empty=True)

        # Verify there's nothing in the index.
        assert ResponseDocType.docs.search().count() == 0

        # Create the record and the chunk and then run it through
        # celery.
        batch_id = 'ou812'
        rec = RecordFactory(batch_id=batch_id)

        chunk = (
            to_class_path(ResponseDocType),
            [item.id for item in responses]
        )
        index_chunk_task.delay(get_index_name(), batch_id, rec.id, chunk)

        self.refresh()

        # Verify everything is in the index now.
        assert ResponseDocType.docs.search().count() == 10

        # Verify the record was marked succeeded.
        rec = Record.objects.get(pk=rec.id)
        assert rec.status == Record.STATUS_SUCCESS
