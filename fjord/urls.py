from django.conf import settings
from django.conf.urls import patterns, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Note: This must come before importing admin because it patches the
# admin.
from fjord.manage_utils import monkeypatch
monkeypatch()

from django.contrib import admin  # noqa

urlpatterns = patterns(
    '',

    (r'', include('fjord.alerts.urls')),
    (r'', include('fjord.analytics.urls')),
    (r'', include('fjord.base.urls')),
    (r'', include('fjord.events.urls')),
    (r'', include('fjord.feedback.urls')),
    (r'', include('fjord.heartbeat.urls')),
    (r'', include('fjord.redirector.urls')),
    (r'', include('fjord.suggest.providers.trigger.urls')),

    (r'', include('django_browserid.urls')),

    (r'^grappelli/', include('grappelli.urls')),
    (r'^admin/', include(admin.site.urls)),
)


# In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
