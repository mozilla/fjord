import logging
import socket
from functools import wraps

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from celery.messaging import establish_connection
from mobility.decorators import mobile_template
from pyelasticsearch.exceptions import (
    ConnectionError, ElasticHttpNotFoundError, Timeout)

from fjord.search.index import get_index, get_index_stats


log = logging.getLogger('i.services')


@mobile_template('{mobile/}login_failure.html')
def login_failure(request, template=None):
    return render(request, template)


@mobile_template('{mobile/}about.html')
def about_view(request, template=None):
    return render(request, template)


def test_memcached(host, port):
    """Connect to memcached.

    :returns: True if test passed, False if test failed.

    """
    try:
        s = socket.socket()
        s.connect((host, port))
        return True
    except Exception as exc:
        log.critical('Failed to connect to memcached (%r): %s' %
                     ((host, port), exc))
        return False
    finally:
        s.close()


def dev_or_authorized(func):
    """Show view for admin and developer instances, else 404"""
    @wraps(func)
    def _dev_or_authorized(request, *args, **kwargs):
        if (request.user.is_superuser or settings.SHOW_STAGE_NOTICE
            or settings.DEBUG):

            return func(request, *args, **kwargs)

        raise Http404
    return _dev_or_authorized


ERROR = 'ERROR'
INFO = 'INFO'


@dev_or_authorized
@never_cache
def monitor_view(request):
    """View for services monitor."""
    # Dict of infrastructure name -> list of output tuples of (INFO,
    # msg) or (ERROR, msg)
    status = {}

    # Note: To add a new component, do your testing and then add a
    # name -> list of output tuples map to status.

    # Check memcached.
    memcache_results = []
    try:
        for cache_name, cache_props in settings.CACHES.items():
            result = True
            backend = cache_props['BACKEND']
            location = cache_props['LOCATION']

            # LOCATION can be a string or a list of strings
            if isinstance(location, basestring):
                location = location.split(';')

            if 'memcache' in backend:
                for loc in location:
                    # TODO: this doesn't handle unix: variant
                    ip, port = loc.split(':')
                    result = test_memcached(ip, int(port))
                    memcache_results.append(
                        (INFO, '%s:%s %s' % (ip, port, result)))

        if not memcache_results:
            memcache_results.append((ERROR, 'memcache is not configured.'))

        elif len(memcache_results) < 2:
            memcache_results.append(
                (ERROR, ('You should have at least 2 memcache servers. '
                         'You have %s.' % len(memcache_results))))

        else:
            memcache_results.append((INFO, 'memcached servers look good.'))

    except Exception as exc:
        memcache_results.append(
            (ERROR, 'Exception while looking at memcached: %s' % str(exc)))

    status['memcached'] = memcache_results

    # Check ES.
    es_results = []
    try:
        get_index_stats()
        es_results.append(
            (INFO, ('Successfully connected to ElasticSearch and index '
                    'exists.')))

    except (ConnectionError, Timeout) as exc:
        es_results.append(
            (ERROR, 'Cannot connect to ElasticSearch: %s' % str(exc)))

    except ElasticHttpNotFoundError:
        es_results.append(
            (ERROR, 'Index "%s" missing.' % get_index()))

    except Exception as exc:
        es_results.append(
            (ERROR, 'Exception while looking at ElasticSearch: %s' % str(exc)))

    status['ElasticSearch'] = es_results

    # Check RabbitMQ.
    rabbitmq_results = []
    try:
        rabbit_conn = establish_connection(connect_timeout=2)
        rabbit_conn.connect()
        rabbitmq_results.append(
            (INFO, 'Successfully connected to RabbitMQ.'))

    except (socket.error, IOError) as exc:
        rabbitmq_results.append(
            (ERROR, 'Error connecting to RabbitMQ: %s' % str(exc)))

    except Exception as exc:
        rabbitmq_results.append(
            (ERROR, 'Exception while looking at RabbitMQ: %s' % str(exc)))

    status['RabbitMQ'] = rabbitmq_results

    status_code = 200

    status_summary = {}
    for component, output in status.items():
        if ERROR in [item[0] for item in output]:
            status_code = 500
            status_summary[component] = False
        else:
            status_summary[component] = True

    return render(request, 'services/monitor.html',
                  {'component_status': status,
                   'status_summary': status_summary},
                  status=status_code)


class IntentionalException(Exception):
    pass


@dev_or_authorized
def throw_error(request):
    """Throw an error for testing purposes."""
    raise IntentionalException("Error raised for testing purposes.")
