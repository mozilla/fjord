from django.conf.urls import patterns, url

from .views import EventAPI


urlpatterns = patterns(
    'fjord.events.views',

    url(r'^api/v1/events/?$', EventAPI.as_view(), name='event-api')
)
