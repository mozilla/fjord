import logging
import socket

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from celery.messaging import establish_connection
from mobility.decorators import mobile_template


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
                    status_summary['memcache'] = result
                    memcache_results.append((ip, port, result))

            if len(memcache_results) < 2:
                status_summary['memcache'] = False
                log.warning('You should have at least 2 memcache servers. '
                            'You have %s.' % len(memcache_results))

        if not memcache_results:
            status_summary['memcache'] = False
            log.warning('Memcache is not configured.')

    except Exception as exc:
        status_summary['memcache'] = False
        log.exception('Exception while looking at memcache')
        errors['memcache'] = '%r %s' % (exc, exc)

    # Check RabbitMQ.
    rabbitmq_results = ''
    try:
        rabbitmq_status = True
        rabbit_conn = establish_connection(connect_timeout=2)
        try:
            rabbit_conn.connect()
            rabbitmq_results = 'Successfully connected to RabbitMQ.'
        except (socket.error, IOError), e:
            rabbitmq_results = ('There was an error connecting to '
                                'RabbitMQ: %s' % str(e))

            rabbitmq_status = False
        status_summary['rabbitmq'] = rabbitmq_status

    except Exception as exc:
        status_summary['rabbitmq'] = False
        log.exception('Exception while looking at rabbitmq')
        errors['rabbitmq'] = '%r %s' % (exc, exc)

    if not all(status_summary.values()):
        status = 500

    return render(request, 'services/monitor.html',
                  {'errors': errors,
                   'memcache_results': memcache_results,
                   'rabbitmq_results': rabbitmq_results,
                   'status_summary': status_summary},
                  status=status)
