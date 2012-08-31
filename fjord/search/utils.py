import logging
import time
from itertools import islice

from django.conf import settings
from django.db import reset_queries

import pyes
from elasticutils.contrib.django import get_es, S

from fjord.search.models import get_mapping_types


log = logging.getLogger('i.search')


def format_time(time_to_go):
    """Returns minutes and seconds string for given time in seconds"""
    if time_to_go < 60:
        return "%ds" % time_to_go
    return  "%dm %ds" % (time_to_go / 60, time_to_go % 60)


def chunked(iterable, n):
    """Returns chunks of n length of iterable

    If len(iterable) % n != 0, then the last chunk will have length
    less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    """
    iterable = iter(iterable)
    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def get_indexing_es(**kwargs):
    """Returns ES instance with 30s timeout for indexing."""
    defaults = {
        'timeout': settings.ES_INDEXING_TIMEOUT
        }
    defaults.update(kwargs)

    return get_es(**defaults)


def delete_index(index):
    """Deletes the specified index."""
    get_indexing_es().delete_index_if_exists(index)


def get_index():
    """Returns the index we're using."""
    return settings.ES_INDEXES['default']


def get_index_stats():
    """Returns a dict of name -> count for documents indexed.

    For example:

    >>> get_index_stats()
    {'simple': 122233}

    :throws pyes.urllib3.MaxRetryError: if it can't connect to elasticsearch
    :throws pyes.exceptions.IndexMissingException: if the index doesn't exist

    """
    stats = {}
    for name, cls in get_mapping_types().items():
        stats[name] = S(cls).count()

    return stats


def recreate_index(es=None):
    """Deletes index if it's there and creates a new one"""
    if es is None:
        es = get_indexing_es()

    mappings = {}
    for name, mt in get_mapping_types().items():
        mapping = mt.get_mapping()
        if mapping is not None:
            mappings[name] = {'properties': mapping}

    index = get_index()

    delete_index(index)

    # There should be no mapping-conflict race here since the index
    # doesn't exist. Live indexing should just fail.

    # Simultaneously create the index and the mappings, so live
    # indexing doesn't get a chance to index anything between the two
    # causing ES to infer a possibly bogus mapping (which causes ES to
    # freak out if the inferred mapping is incompatible with the
    # explicit mapping).

    es.create_index(index, settings={'mappings': mappings})


def get_indexable(percent=100, mapping_types=None):
    """Returns a list of (class, iterable) for all the things to index

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.
    :arg mapping_types: List of mapping types to index. Defaults to
        indexing all mapping types.

    """

    to_index = []
    percent = float(percent) / 100

    for name, cls in get_mapping_types(mapping_types).items():
        indexable = cls.get_indexable()
        if percent < 1:
            indexable = indexable[:int(indexable.count() * percent)]
        to_index.append((cls, indexable))

    return to_index


def index_chunk(cls, chunk, reraise=False, es=None):
    if es is None:
        es = get_indexing_es()

    try:
        for id_ in chunk:
            try:
                cls.index(cls.extract_document(id_), bulk=True, es=es)
            except Exception:
                log.exception('Unable to extract/index document (id: %d)', id_)
                if reraise:
                    raise

    finally:
        # Try to do these things, but if we fail, it's probably the
        # case that many things are broken, so just move on.
        try:
            es.flush_bulk(forced=True)
            es.refresh(get_index(), timesleep=0)
        except Exception:
            log.exception('Unable to flush/refresh')


def es_reindex_cmd(percent=100, mapping_types=None):
    """Rebuild ElasticSearch indexes

    :arg percent: 1 to 100--the percentage of the db to index
    :arg mapping_types: list of mapping types to index

    """
    es = get_indexing_es()

    log.info('Wiping and recreating %s....', get_index())
    recreate_index(es=es)

    if mapping_types:
        indexable = get_indexable(percent, mapping_types)
    else:
        indexable = get_indexable(percent)

    start_time = time.time()

    for cls, indexable in indexable:
        cls_start_time = time.time()
        total = len(indexable)

        if total == 0:
            continue

        log.info('reindex %s. %s to index....',
                 cls.get_mapping_type_name(), total)

        i = 0
        for chunk in chunked(indexable, 1000):
            index_chunk(cls, chunk, es=es)

            i += len(chunk)
            time_to_go = (total - i) * ((time.time() - start_time) / i)
            per_1000 = (time.time() - start_time) / (i / 1000.0)
            log.info('%s/%s... (%s to go, %s per 1000 docs)', i, total,
                     format_time(time_to_go),
                     format_time(per_1000))

            # We call this every 1000 or so because we're
            # essentially loading the whole db and if DEBUG=True,
            # then Django saves every sql statement which causes
            # our memory to go up up up. So we reset it and that
            # makes things happier even in DEBUG environments.
            reset_queries()

        delta_time = time.time() - cls_start_time
        log.info('done! (%s, %s per 1000 docs)',
                 format_time(delta_time),
                 format_time(delta_time / (total / 1000.0)))

    delta_time = time.time() - start_time
    log.info('done! (total time: %s)', format_time(delta_time))


def es_status_cmd(checkindex=False):
    """Shows elastic search index status"""
    try:
        try:
            mt_stats = get_index_stats()
        except pyes.exceptions.IndexMissingException:
            mt_stats = None

    except pyes.urllib3.MaxRetryError:
        log.error('Your elasticsearch process is not running or ES_HOSTS '
                  'is set wrong in your settings_local.py file.')
        return

    log.info('Settings:')
    log.info('  ES_HOSTS              : %s', settings.ES_HOSTS)
    log.info('  ES_INDEX_PREFIX       : %s', settings.ES_INDEX_PREFIX)
    log.info('  ES_INDEXES            : %s', settings.ES_INDEXES)

    log.info('Index (%s) stats:', get_index())

    if mt_stats is None:
        log.info('  Index does not exist. (%s)', get_index())
    else:
        log.info('  Index (%s):', get_index())
        for name, count in mt_stats.items():
            log.info('    %-20s: %d', name, count)
