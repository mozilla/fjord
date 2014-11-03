from django.conf import settings
from django.conf.urls import patterns, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse

# Note: This must come before importing admin because it patches the
# admin.
from fjord.base.monkeypatches import patch
patch()

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',

    (r'', include('fjord.analytics.urls')),
    (r'', include('fjord.base.urls')),
    (r'', include('fjord.events.urls')),
    (r'', include('fjord.feedback.urls')),
    (r'', include('fjord.heartbeat.urls')),

    # Generate a robots.txt
    (
        r'^robots\.txt$',
        lambda r: HttpResponse(
            ("User-agent: *\n%s: /" % (
                'Allow' if settings.ENGAGE_ROBOTS else 'Disallow')),
            content_type="text/plain"
        )
    ),

    (r'^browserid/', include('django_browserid.urls')),

    (r'^grappelli/', include('grappelli.urls')),
    (r'^admin/', include(admin.site.urls)),
)


# In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
