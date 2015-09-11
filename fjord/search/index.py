import logging
import time
from itertools import islice

from django.conf import settings
from django.db import reset_queries
from django.shortcuts import render
from django.utils.decorators import decorator_from_middleware_with_args

import requests
from elasticsearch.exceptions import (
    ConnectionError,
    ElasticsearchException,
    NotFoundError
)
from elasticsearch.helpers import bulk_index
from elasticsearch_dsl import DocType, Search, Index
from elasticsearch_dsl.connections import connections

# Note: This module should not import any Fjord modules. Otherwise we
# get into import recursion issues.


log = logging.getLogger('i.search')


ES_EXCEPTIONS = (
    ElasticsearchException,
)


_doctypes = {}


def register_doctype(doctype):
    """Registers a doctype that Fjord should know about

    :arg doctype: DocType subclass

    :returns: doctype class so this can be used as a class
        decorator
    """
    _doctypes[doctype._doc_type.name] = doctype
    return doctype


def get_es(alias='default'):
    """Retrieve Elasticsearch instance

    :arg alias: the alias in ES_URLS for this Elasticsearch connection

    """
    return connections.get_connection(alias=alias)


class ESExceptionMiddleware(object):
    """Middleware to handle Elasticsearch errors.

    HTTP 503
      Returned when any elasticsearch exception is thrown.

      Template variables:

      * error: A string version of the exception thrown.

    :arg error_template: The template to use when Elasticsearch isn't
        working properly, is missing an index, or something along
        those lines.

    """

    def __init__(self, error_template):
        self.error_template = error_template

    def process_exception(self, request, exception):
        if issubclass(exception.__class__, ES_EXCEPTIONS):
            response = render(request, self.error_template,
                              {'error': exception})
            response.status_code = 503
            return response


# The following decorator wraps a Django view and handles Elasticsearch errors.
#
# This wraps a Django view and returns 503 status codes and pages if
# things go awry.
#
# See the above middleware for explanation of the arguments.
#
# Example:
#
#     # This creates a home_view and decorates it to use the
#     # default templates.
#
#     @es_required_or_50x(error_template='foo/bar.html')
#     def home_view(request):
#         ...
es_required_or_50x = decorator_from_middleware_with_args(
    ESExceptionMiddleware)


def es_analyze(text, analyzer=None):
    """Returns analysis of text.

    :arg text: the text to analyze

    :arg analyzer: The name of the analyzer to use. Defaults to
        snowball which is an English-settings analyzer.

    :returns: list of dicts each describing a token

    """
    es = get_es()
    index = get_index_name()
    analyzer = analyzer or 'snowball'

    ret = es.indices.analyze(index, body=text, analyzer=analyzer)

    return ret['tokens']


def get_doctypes(doctypes=None):
    """Returns dict of name -> DocType subclass for given doctype names

    :arg doctypes: list of doctype names to return

    :returns: dict of name -> DocType subclass

    """
    if doctypes is None:
        return _doctypes

    return dict((key, val) for key, val in _doctypes.items()
                if key in doctypes)


def get_index_name():
    """Returns the name of the index we're using."""

    # Note: This could probably be defined in utils, but it's defined
    # here because otherwise models imports utils and utils imports
    # models and that turns into a mess.
    return '%s-%s' % (settings.ES_INDEX_PREFIX, settings.ES_INDEXES['default'])


ALL_DOCS = object()


class FjordDocTypeManager(object):
    """Similar to ModelManager, this thinks about groups of objects"""
    @classmethod
    def get_doctype(cls):
        return None

    @classmethod
    def get_indexable(cls):
        return (
            cls.get_doctype().get_model().objects
            .order_by('id')
            .values_list('id', flat=True)
        )

    @classmethod
    def search(cls):
        return Search(
            using=get_es(),
            index=get_index_name(),
            doc_type=cls.get_doctype()
        )

    @classmethod
    def delete(cls, item_id):
        es = get_es()
        es.delete(
            index=get_index_name(),
            doc_type=cls.get_doctype()._doc_type.name,
            id=item_id
        )

    @classmethod
    def bulk_index(cls, docs=ALL_DOCS):
        es = get_es()

        if docs is ALL_DOCS:
            docs = [cls.get_doctype().extract_doc(obj)
                    for obj in cls.get_indexable()]

        if not docs:
            return

        bulk_index(
            es,
            docs,
            index=get_index_name(),
            doc_type=cls.get_doctype()._doc_type.name,
            raise_on_error=True
        )


class FjordDocType(DocType):
    """Slightly enhanced DocType to make it easier to connect things"""
    @classmethod
    def get_model(cls):
        return None

    @classmethod
    def extract_doc(cls, resp, with_id=True):
        """Convert model instance to a dict of values

        This can be used with ``FjordDocType.from_obj()`` to create a
        ``FjordDocType`` instance or it can be used for bulk indexing.

        :arg resp: a model instance
        :arg with_id: whether or not to include the ``_id`` value--include
            it when you're bulk indexing

        :returns: a dict

        """
        raise NotImplemented

    @classmethod
    def from_obj(cls, obj):
        """Takes a Django model instance and creates a DocType from it"""
        return cls(**cls.extract_doc(obj, with_id=False))


def format_time(time_to_go):
    """Return minutes and seconds string for given time in seconds.

    :arg time_to_go: Number of seconds to go.

    :returns: string representation of how much time to go

    """
    if time_to_go < 60:
        return '%ds' % time_to_go
    return '%dm %ds' % (time_to_go / 60, time_to_go % 60)


def create_batch_id():
    """Returns a batch_id for indexing via the admin"""
    # TODO: This is silly, but it's a good enough way to distinguish
    # between batches by looking at a Record. This is just over the
    # number of seconds in a day.
    return str(int(time.time()))[-6:]


def chunked(iterable, n):
    """Return chunks of n length of iterable.

    If ``len(iterable) % n != 0``, then the last chunk will have
    length less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    :arg iterable: the iterable
    :arg n: the chunk length

    :returns: generator of chunks from the iterable
    """
    iterable = iter(iterable)
    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def get_indexes(all_indexes=False):
    """Return list of (name, count) tuples for indexes.

    :arg all_indexes: True if you want to see all indexes and
        False if you want to see only indexes prefexed with
        ``settings.ES_INDEX_PREFIX``.

    :returns: list of (name, count) tuples.

    """
    status = get_es().indices.status()
    indexes = status['indices']

    if not all_indexes:
        indexes = dict((k, v) for k, v in indexes.items()
                       if k.startswith(settings.ES_INDEX_PREFIX))

    indexes = [(k, v['docs']['num_docs']) for k, v in indexes.items()]

    return indexes


def get_index_stats():
    """Return dict of name -> count for documents indexed.

    For example:

    >>> get_index_stats()
    {'response_doc_type': 122233}

    .. Note::

       This infers the index to use from the registered doctypes.

    :returns: doctype name -> count for documents indexes.

    :throws elasticsearch.exceptions.ConnectionError: if there's a
        connection error
    :throws elasticsearch.exceptions.NotFoundError: if the
        index doesn't exist

    """
    stats = {}
    for name, cls in get_doctypes().items():
        stats[name] = cls.docs.search().count()

    return stats


def recreate_index():
    """Delete index if it's there and creates a new one"""
    index = Index(name=get_index_name(), using='default')

    for name, doc_type in get_doctypes().items():
        index.doc_type(doc_type)

    # Delete the index if it exists.
    try:
        index.delete()
    except NotFoundError:
        pass

    # Note: There should be no mapping-conflict race here since the
    # index doesn't exist. Live indexing should just fail.

    # Create the index with the mappings all at once.
    index.create()


def get_indexable(percent=100, doctypes=None):
    """Returns list of (cls, indexable objects) tuples

    :arg percent: 0 through 100; allows you to get some and not all
        of the possible things to index for a given doctype
    :arg doctypes: list of doctype names for the doctypes you
        want indexable objects for

    :returns: list of (cls, indexable) tuples

    """
    to_index = []
    percent = float(percent) / 100

    for name, cls in get_doctypes(doctypes).items():
        indexable = cls.docs.get_indexable()
        if percent < 1:
            indexable = indexable[:int(indexable.count() * percent)]
        to_index.append((cls, indexable))

    return to_index


def index_chunk(cls, id_list):
    """Index a chunk of documents.

    :arg cls: The MappingType class.
    :arg id_list: Iterable of ids of that MappingType to index.

    """
    for ids in chunked(id_list, 1000):
        obj_list = cls.get_model().objects.filter(id__in=ids)
        cls.docs.bulk_index(docs=[cls.extract_doc(obj) for obj in obj_list])

    if settings.DEBUG:
        # Nix queries so that this doesn't become a complete
        # memory hog and make Will's computer sad when DEBUG=True.
        reset_queries()


def requires_good_connection(fun):
    """Decorator that logs an error on connection issues

    9 out of 10 doctors say that connection errors are usually because
    ES_URLS is set wrong. This catches those errors and helps you out
    with fixing it.

    """
    def _requires_good_connection(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except ConnectionError:
            log.error('Either your ElasticSearch process is not quite '
                      'ready to rumble, is not running at all, or ES_URLS '
                      'is set wrong in your settings_local.py file.')
    return _requires_good_connection


@requires_good_connection
def es_reindex_cmd(percent=100, doctypes=None):
    """Rebuild ElasticSearch indexes.

    :arg percent: 1 to 100--the percentage of the db to index
    :arg doctypes: list of doctypes to index

    """
    es = get_es()

    log.info('Wiping and recreating %s....', get_index_name())
    recreate_index()

    # Shut off auto-refreshing.
    index_settings = es.indices.get_settings(index=get_index_name())
    old_refresh = (index_settings
                   .get(get_index_name(), {})
                   .get('settings', {})
                   .get('index.refresh_interval', '1s'))

    try:
        es.indices.put_settings(
            index=get_index_name(), body={'index': {'refresh_interval': '-1'}})

        indexable = get_indexable(percent, doctypes)

        start_time = time.time()
        for cls, indexable in indexable:
            cls_start_time = time.time()
            total = len(indexable)

            if total == 0:
                continue

            log.info('Reindex %s. %s to index....',
                     cls._doc_type.name, total)

            i = 0
            for chunk in chunked(indexable, 1000):
                chunk_start_time = time.time()
                index_chunk(cls, chunk)

                i += len(chunk)
                time_to_go = (total - i) * ((time.time() - cls_start_time) / i)
                per_1000 = (time.time() - cls_start_time) / (i / 1000.0)
                this_1000 = time.time() - chunk_start_time

                log.info(
                    '   %s/%s %s... (%s/1000 avg, %s ETA)',
                    i,
                    total,
                    format_time(this_1000),
                    format_time(per_1000),
                    format_time(time_to_go)
                )

            delta_time = time.time() - cls_start_time
            log.info('   done! (%s total, %s/1000 avg)',
                     format_time(delta_time),
                     format_time(delta_time / (total / 1000.0)))

        delta_time = time.time() - start_time
        log.info('Done! (total time: %s)', format_time(delta_time))

    finally:
        es.indices.put_settings(
            index=get_index_name(),
            body={'index': {'refresh_interval': old_refresh}})
        es.indices.refresh(get_index_name())


@requires_good_connection
def es_delete_cmd(index_name):
    """Delete a specified index

    :arg index_name: name of index to delete

    """
    indexes = [name for name, count in get_indexes()]

    if index_name not in indexes:
        log.error('Index "%s" is not a valid index.', index_name)
        if not indexes:
            log.error('There are no valid indexes.')
        else:
            log.error('Valid indexes: %s', ', '.join(indexes))
        return

    ret = raw_input(
        'Are you sure you want to delete "%s"? (yes/no) ' % index_name
    )
    if ret != 'yes':
        return

    log.info('Deleting index "%s"...', index_name)
    index = Index(name=index_name, using='default')
    try:
        index.delete()
    except NotFoundError:
        pass
    log.info('Done!')


@requires_good_connection
def es_status_cmd(log=log):
    """Show ElasticSearch index status

    :arg log: the logger to use

    """
    log.info('Settings:')
    log.info('  ES_URLS               : %s', settings.ES_URLS)
    log.info('  ES_INDEX_PREFIX       : %s', settings.ES_INDEX_PREFIX)
    log.info('  ES_INDEXES            : %s', settings.ES_INDEXES)

    # FIXME - can do this better with elasticsearch API.
    try:
        es_deets = requests.get(settings.ES_URLS[0]).json()
        log.info('  Elasticsearch version : %s', es_deets['version']['number'])
    except requests.exceptions.RequestException:
        log.info('  Could not connect to Elasticsearch')

    log.info('Index (%s) stats:', get_index_name())

    try:
        mt_stats = get_index_stats()
        log.info('  Index (%s):', get_index_name())
        for name, count in mt_stats.items():
            log.info('    %-20s: %d', name, count)

    except NotFoundError:
        log.info('  Index does not exist. (%s)', get_index_name())
