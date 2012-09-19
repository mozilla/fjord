import datetime
import logging
import sys

from celery.decorators import task
from multidb.pinning import pin_this_thread, unpin_this_thread

from fjord.search.index import index_chunk
from fjord.search.models import Record


log = logging.getLogger('i.task')


# Note: If you reduce the length of RETRY_TIMES, it affects all tasks
# currently in the celery queue---they'll throw an IndexError.
RETRY_TIMES = (
    60,  # 1 minute
    5 * 60,  # 5 minutes
    10 * 60,  # 10 minutes
    30 * 60,  # 30 minutes
    60 * 60,  # 60 minutes
    )
MAX_RETRIES = len(RETRY_TIMES)


@task
def index_chunk_task(index, batch_id, rec_id, chunk):
    """Index a chunk of things.

    :arg index: the name of the index to index to
    :arg batch_id: the name for the batch this chunk belongs to
    :arg rec_id: the id for the record for this task
    :arg chunk: a (class, id_list) of things to index
    """
    cls, id_list = chunk

    try:
        # Pin to master db to avoid replication lag issues and stale
        # data.
        pin_this_thread()

        # Update record data.
        rec = Record.objects.get(pk=rec_id)
        rec.start_time = datetime.datetime.now()
        rec.message = u'Reindexing into %s' % index
        rec.status = Record.STATUS_IN_PROGRESS
        rec.save()

        index_chunk(cls, id_list, reraise=True)

        rec.mark_success()

    except Exception:
        rec.mark_fail(u'Errored out %s %s' % (
                sys.exc_type, sys.exc_value))
        raise

    finally:
        unpin_this_thread()


@task
def index_item_task(mapping_type, item_id):
    """Index an item given it's mapping_type and id."""
    try:
        doc = mapping_type.extract_document(item_id)
        mapping_type.index(doc)

    except Exception as exc:
        log.exception(str(exc))
        retries = index_item_task.request.retries
        if retries >= MAX_RETRIES:
            raise
        retry_time = RETRY_TIMES[retries]
        index_item_task.retry(exc=exc, countdown=retry_time)


@task
def unindex_item_task(mapping_type, item_id):
    """Remove an item from the index, given it's mapping_type and id."""
    try:
        doc = mapping_type.extract_document(item_id)
        mapping_type.unindex(doc['id'])

    except Exception as exc:
        log.exception(str(exc))
        retries = unindex_item_task.request.retries
        if retries >= MAX_RETRIES:
            raise
        retry_time = RETRY_TIMES[retries]
        unindex_item_task.retry(exc=exc, countdown=retry_time)
