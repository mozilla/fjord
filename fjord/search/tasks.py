import datetime
import logging
import sys

from django.db.models.signals import post_save, pre_delete

from celery.decorators import task
from multidb.pinning import pin_this_thread, unpin_this_thread

from fjord.search.index import index_chunk
from fjord.search.models import Record


log = logging.getLogger('i.task')


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
def index_item_task(index_cls, item_id):
    doc = index_cls.extract_document(item_id)
    index_cls.index(doc)


def _live_index_handler(sender, **kwargs):
    if 'signal' not in kwargs or 'instance' not in kwargs:
        return

    instance = kwargs['instance']

    if kwargs['signal'] == post_save:
        index_item_task(instance.get_index(), instance.id)
        return

    if kwargs['signal'] == pre_delete:
        # TODO: How do I delete item from the index?
        raise NotImplemented


def register_live_index(model_cls):
    """Register a model and index for auto indexing."""
    post_save.connect(_live_index_handler, model_cls)
    pre_delete.connect(_live_index_handler, model_cls)
