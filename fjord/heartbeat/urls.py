from django.conf.urls import patterns, url

from fjord.heartbeat.analyzer_views import SurveyCreateView, SurveyUpdateView
from fjord.heartbeat.api_views import HeartbeatV2API


urlpatterns = patterns(
    'fjord.heartbeat.views',

    url(r'^api/v2/hb/?$', HeartbeatV2API.as_view(), name='heartbeat-api')
)

# Analyzer-group-only views
urlpatterns += patterns(
    'fjord.heartbeat.analyzer_views',

    url(r'^analytics/hbdata(?:/(?P<answerid>\d+))?/?$', 'hb_data',
        name='hb_data'),
    url(r'^analytics/hberrorlog(?:/(?P<errorid>\d+))?/?$', 'hb_errorlog',
        name='hb_errorlog'),
    url(r'^analytics/hbsurveys/?$',
        SurveyCreateView.as_view(),
        name='hb_surveys'),
    url(r'^analytics/hbsurveys/(?P<pk>\d+)/update/$',
        SurveyUpdateView.as_view(),
        name='hb_surveys_update'),
)
