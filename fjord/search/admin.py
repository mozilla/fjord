import logging
from datetime import datetime

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render

from pyelasticsearch.exceptions import (
    ConnectionError, ElasticHttpNotFoundError, Timeout)

from fjord.search.index import (
    chunked, get_index, get_index_stats, get_indexes, get_indexable,
    recreate_index, create_batch_id)
from fjord.search.models import Record
from fjord.search.tasks import index_chunk_task


log = logging.getLogger('i.search')


CHUNK_SIZE = 50000


def handle_reset(request):
    """Mark outstanding Records as failed.

    Why? You'd want to reset the system if it gets itself wedged
    thinking there are outstanding tasks, but there aren't. This
    lets you fix that.

    """
    for rec in Record.outstanding():
        rec.mark_fail('Cancelled.')
    return HttpResponseRedirect(request.path)


def handle_reindex(request):
    """Caculate chunks and kick off indexing tasks."""
    index = get_index()

    batch_id = create_batch_id()

    # Break up all the things we want to index into chunks. This
    # chunkifies by class then by chunk size.
    chunks = []
    for cls, indexable in get_indexable():
        chunks.extend(
            (cls, chunk) for chunk in chunked(indexable, CHUNK_SIZE))

    # The previous lines do a lot of work and take some time to
    # execute.  So we wait until here to wipe and rebuild the
    # index. That reduces the time that there is no index by a little.
    recreate_index()

    for cls, id_list in chunks:
        chunk_name = '%s %d -> %d' % (cls.get_mapping_type_name(),
                                      id_list[0], id_list[-1])
        rec = Record(batch_id=batch_id, name=chunk_name)
        rec.save()
        index_chunk_task.delay(index, batch_id, rec.id, (cls, id_list))

    return HttpResponseRedirect(request.path)


def search_admin_view(request):
    """Render the admin view containing search tools"""
    error_messages = []
    stats = None
    indexes = []

    reset_requested = 'reset' in request.POST
    if reset_requested:
        try:
            return handle_reset(request)
        except Exception as exc:
            error_messages.append(u'Error: %s' % exc.message)

    reindex_requested = 'reindex' in request.POST
    if reindex_requested:
        try:
            return handle_reindex(request)
        except Exception as exc:
            error_messages.append(u'Error: %s' % exc.message)

    try:
        # This gets index stats, but also tells us whether ES is in
        # a bad state.
        try:
            stats = get_index_stats()
        except ElasticHttpNotFoundError:
            stats = None
        indexes = get_indexes()
        indexes.sort(key=lambda m: m[0])

    except (ConnectionError, Timeout):
        error_messages.append('Error: Elastic Search is not set up on this '
                              'machine or timed out trying to respond. '
                              '(ConnectionError/Timeout)')
    except ElasticHttpNotFoundError:
        error_messages.append('Error: Index is missing. Press the reindex '
                              'button below. (ElasticHttpNotFoundError)')

    outstanding_records = Record.outstanding()
    recent_records = Record.objects.order_by('-creation_time')[:20]

    return render(request, 'admin/search_admin_view.html', {
            'title': 'Search',
            'mapping_type_stats': stats,
            'indexes': indexes,
            'index': get_index(),
            'error_messages': error_messages,
            'recent_records': recent_records,
            'outstanding_records': outstanding_records,
            'now': datetime.now(),
            })


admin.site.register_view('search-admin-view', search_admin_view,
                         'ElasticSearch - Index Maintenance')
