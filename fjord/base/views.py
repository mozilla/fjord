import logging
import socket

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from celery.messaging import establish_connection
from mobility.decorators import mobile_template
import pyes

from fjord.search.index import get_index_stats


log = logging.getLogger('i.services')


@mobile_template('{mobile/}home.html')
def home_view(request, template=None):
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


@never_cache
def monitor_view(request):
    """View for services monitor."""
    # For each check, a boolean pass/fail to show in the template.
    status_summary = {}
    errors = {}
    status = 200

    # Check memcached.
    memcache_results = []
    memcache_status = False
    try:
        status_summary['memcache'] = True
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
                    memcache_results.append('%s:%s %s' % (ip, port, result))

        if not memcache_results:
            memcache_results.append('memcache is not configured.')
            log.warning('Memcache is not configured.')

        elif len(memcache_results) < 2:
            msg = ('You should have at least 2 memcache servers. '
                   'You have %s.' % len(memcache_results))
            log.warning(msg)
            memcache_results.append(msg)

        else:
            memcache_status = True
            memcache_results.append('memcache servers look good.')

    except Exception as exc:
        log.exception('Exception while looking at memcache')
        errors['memcache'] = '%r %s' % (exc, exc)

    status_summary['memcache'] = memcache_status

    # Check ES.
    es_results = ''
    es_status = False
    try:
        get_index_stats()
        es_results = ('Successfully connected to ElasticSearch and index '
                      'exists.')
        es_status = True

    except pyes.urllib3.MaxRetryError as exc:
        es_results = ('Cannot connect to ElasticSearch: %s' % str(exc))

    except pyes.exceptions.IndexMissingException:
        es_results = 'Index missing.'

    status_summary['es'] = es_status

    # Check RabbitMQ.
    rabbitmq_results = ''
    rabbitmq_status = False
    try:
        rabbit_conn = establish_connection(connect_timeout=2)
        rabbit_conn.connect()
        rabbitmq_results = 'Successfully connected to RabbitMQ.'
        rabbitmq_status = True

    except (socket.error, IOError) as exc:
        rabbitmq_results = ('There was an error connecting to '
                            'RabbitMQ: %s' % str(exc))
        errors['rabbitmq'] = '%r %s' % (exc, exc)

    except Exception as exc:
        log.exception('Exception while looking at rabbitmq')
        rabbitmq_results = ('Exception while looking at rabbitmq: %s' %
                            str(exc))
        errors['rabbitmq'] = '%r %s' % (exc, exc)

    status_summary['rabbitmq'] = rabbitmq_status

    if not all(status_summary.values()):
        errors['statii'] = repr(status_summary.values())
        status = 500

    return render(request, 'services/monitor.html',
                  {'errors': errors,
                   'es_results': es_results,
                   'memcache_results': memcache_results,
                   'rabbitmq_results': rabbitmq_results,
                   'status_summary': status_summary},
                  status=status)
