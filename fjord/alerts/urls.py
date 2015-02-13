from django.conf.urls import patterns, url

from fjord.alerts import api_views


urlpatterns = patterns(
    'fjord.feedback.api_views',

    url(r'^api/v1/alerts/alert/$',
        api_views.AlertsAPI.as_view(), name='alerts-api')
)
