import re
import sys

from django import VERSION
from django.contrib import admin
from django.shortcuts import render
from django.views import debug

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
    return render(request, 'admin/env_view.html', {
        'pythonver': sys.version,
        'djangover': VERSION
    })

admin.site.register_view(path='env',
                         name='Environment',
                         view=env_view)
