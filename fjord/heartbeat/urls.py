from django.conf.urls import patterns, url

from .views import HeartbeatAPI


urlpatterns = patterns(
    'fjord.heartbeat.views',

    url(r'^api/v1/hb/?$', HeartbeatAPI.as_view(), name='heartbeat-api')
)
