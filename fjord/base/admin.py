from datetime import datetime
import re
import sys
import time

from django import VERSION
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import debug

from celery import current_app

from .tasks import celery_health_task


def timezone_view(request):
    """Admin view showing times and timezones in data."""
    # Note: This is an admin page that gets used once in a blue moon.
    # As such, I'm taking some liberties (hand-indexing the response,
    # time.sleep, etc) that I would never take if it was used more
    # often or was viewable by users. If these two assumptions ever
    # change, then this should be rewritten.

    from elasticutils.contrib.django import get_es

    from fjord.feedback.models import Response, ResponseMappingType
    from fjord.feedback.tests import ResponseFactory
    from fjord.search.index import get_index

    server_time = datetime.now()

    # Create a new response.
    resp = ResponseFactory.create()
    resp_time = resp.created

    # Index the response by hand so we know it gets to Elasticsearch. Otherwise
    # it gets done by celery and we don't know how long that'll take.
    doc = ResponseMappingType.extract_document(resp.id)
    ResponseMappingType.index(doc, resp.id)

    # Fetch the response from the db.
    resp = Response.objects.get(id=resp.id)
    resp2_time = resp.created

    # Refresh and sleep 5 seconds as a hand-wavey way to make sure
    # that Elasticsearch has had time to refresh the index.
    get_es().indices.refresh(get_index())
    time.sleep(5)

    es_time = ResponseMappingType.search().filter(id=resp.id)[0].created

    # Delete the test response we created.
    resp.delete()

    return render(request, 'admin/timezone_view.html', {
        'server_time': server_time,
        'resp_time': resp_time,
        'resp2_time': resp2_time,
        'es_time': es_time
    })

admin.site.register_view(path='timezone',
                         name='Timezone - Time/Timezone stuff',
                         view=timezone_view)


def settings_view(request):
    """Admin view that displays the django settings."""
    settings = debug.get_safe_settings()
    sorted_settings = [{'key': key, 'value': settings[key]}
                       for key in sorted(settings.keys())]

    return render(request, 'admin/settings_view.html', {
        'settings': sorted_settings,
        'title': 'App Settings'
    })


admin.site.register_view(path='settings',
                         name='Settings - App settings',
                         view=settings_view)


def celery_health_view(request):
    """Admin view that displays the celery configuration and health."""
    if request.method == 'POST':
        celery_health_task.delay(datetime.now())
        messages.success(request, 'Health task created.')
        return HttpResponseRedirect(request.path)

    capital = re.compile('^[A-Z]')
    settings = [key for key in dir(current_app.conf) if capital.match(key)]
    sorted_settings = [
        {
            'key': key,
            'value': ('*****' if 'password' in key.lower()
                      else getattr(current_app.conf, key))
        } for key in sorted(settings)
    ]

    return render(request, 'admin/celery_health_view.html', {
        'settings': sorted_settings,
        'title': 'Celery Settings and Health'
    })


admin.site.register_view(path='celery',
                         name='Settings - Celery Settings and Health',
                         view=celery_health_view)


def env_view(request):
    """Admin view that displays the wsgi env."""
    return render(request, 'admin/env_view.html', {
        'pythonver': sys.version,
        'djangover': VERSION
    })

admin.site.register_view(path='env',
                         name='Environment',
                         view=env_view)
