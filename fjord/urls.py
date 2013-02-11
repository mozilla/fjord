from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse

from funfactory.monkeypatches import patch
patch()

from django.contrib import admin
from adminplus import AdminSitePlus

admin.site = AdminSitePlus()
admin.autodiscover()


urlpatterns = patterns('',

    (r'', include('fjord.analytics.urls')),
    (r'', include('fjord.base.urls')),
    (r'', include('fjord.feedback.urls')),
    (r'', include('fjord.search.urls')),

    url(r'stub', lambda r: HttpResponse('this is a stub'), name='stub'),

    # Generate a robots.txt
    (r'^robots\.txt$',
        lambda r: HttpResponse(
            "User-agent: *\n%s: /" % 'Allow' if settings.ENGAGE_ROBOTS else 'Disallow',
            mimetype="text/plain"
        )
    ),

    (r'^browserid/', include('django_browserid.urls')),

    (r'^admin/', include(admin.site.urls)),
)


## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
