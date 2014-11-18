import re

from django import http
from django.contrib import admin
from django.shortcuts import render
from django.views import debug

import jinja2
from celery import current_app


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


def celery_settings_view(request):
    """Admin view that displays the celery configuration."""
    capital = re.compile('^[A-Z]')
    settings = [key for key in dir(current_app.conf) if capital.match(key)]
    sorted_settings = [
        {'key': key,
         'value': ('*****' if 'password' in key.lower()
                   else getattr(current_app.conf, key))}
        for key in sorted(settings)]

    return render(request, 'admin/settings_view.html', {
        'settings': sorted_settings,
        'title': 'Celery Settings'
    })


admin.site.register_view(path='celery',
                         name='Settings - Celery Settings',
                         view=celery_settings_view)


def env_view(request):
    """Admin view that displays the wsgi env."""
    return http.HttpResponse(u'<pre>%s</pre>' % (jinja2.escape(request)))

admin.site.register_view(path='env',
                         name='WSGI Environment',
                         view=env_view)
