from django.conf.urls import patterns, url

from .api_views import HeartbeatV2API


urlpatterns = patterns(
    'fjord.heartbeat.views',

    url(r'^api/v2/hb/?$', HeartbeatV2API.as_view(), name='heartbeat-api')
)
