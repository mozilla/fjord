import datetime
import logging
import sys

from django.conf import settings
from django.db.models.signals import post_save, pre_delete

from celery import task
from multidb.pinning import pin_this_thread, unpin_this_thread

from fjord.search.index import index_chunk
from fjord.search.models import Record
from fjord.search.utils import from_class_path, to_class_path


log = logging.getLogger('i.task')


@task()
def index_chunk_task(index, batch_id, rec_id, chunk):
    """Index a chunk of things.

    :arg index: the name of the index to index to
    :arg batch_id: the name for the batch this chunk belongs to
    :arg rec_id: the id for the record for this task
    :arg chunk: a (cls_path, id_list) of things to index
    """
    cls_path, id_list = chunk
    cls = from_class_path(cls_path)
    rec = None

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

        index_chunk(cls, id_list)

        rec.mark_success()

    except Exception:
        if rec is not None:
            rec.mark_fail(u'Errored out %s %s' % (
                sys.exc_type, sys.exc_value))
        raise

    finally:
        unpin_this_thread()


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


@task()
def index_item_task(cls_path, item_id, **kwargs):
    """Index an item given it's mapping_type cls_path and id"""
    mapping_type = from_class_path(cls_path)
    retries = kwargs.get('task_retries', 0)
    log.debug('Index attempt #%s', retries)
    try:
        doc = mapping_type.extract_document(item_id)
        mapping_type.index(doc, item_id)

    except Exception as exc:
        log.exception("Error while live indexing %s %d: %s",
                      mapping_type, item_id, exc)
        if retries >= MAX_RETRIES:
            raise
        retry_time = RETRY_TIMES[retries]

        args = (mapping_type, item_id)
        if not kwargs:
            # Celery is lame. It requires that kwargs be non empty, but when
            # EAGER is true, it provides empty kwargs.
            kwargs['_dummy'] = True
        index_item_task.retry(args, kwargs, exc, countdown=retry_time)


@task()
def unindex_item_task(cls_path, item_id, **kwargs):
    """Remove item from index, given it's mapping_type class_path and id"""
    mapping_type = from_class_path(cls_path)
    try:
        mapping_type.unindex(item_id)

    except Exception as exc:
        retries = kwargs.get('task_retries', 0)
        log.exception("Error while live unindexing %s %d: %s",
                      mapping_type, item_id, exc)
        if retries >= MAX_RETRIES:
            raise
        retry_time = RETRY_TIMES[retries]

        args = (mapping_type, item_id)
        if not kwargs:
            # Celery is lame. It requires that kwargs be non empty, but when
            # EAGER is true, it provides empty kwargs.
            kwargs['_dummy'] = True
        unindex_item_task.retry(args, kwargs, exc, countdown=retry_time)


def _live_index_handler(sender, **kwargs):
    if (not settings.ES_LIVE_INDEX
            or 'signal' not in kwargs
            or 'instance' not in kwargs):
        return

    instance = kwargs['instance']

    if kwargs['signal'] == post_save:
        cls_path = to_class_path(instance.get_mapping_type())
        index_item_task.delay(cls_path, instance.id)

    elif kwargs['signal'] == pre_delete:
        cls_path = to_class_path(instance.get_mapping_type())
        unindex_item_task.delay(cls_path, instance.id)


def register_live_index(model_cls):
    """Register a model and index for auto indexing."""
    uid = str(model_cls) + 'live_indexing'
    post_save.connect(_live_index_handler, model_cls, dispatch_uid=uid)
    pre_delete.connect(_live_index_handler, model_cls, dispatch_uid=uid)
    # Enable this to be used as decorator.
    return model_cls
