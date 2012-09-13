from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

from fjord.base import views


urlpatterns = patterns('fjord.base.views',

    url(r'^$', 'home_view', name='home_view'),

    url(r'^about$', redirect_to, {'url': 'stub'}, name='about'),

    url(r'^services/monitor$', views.monitor_view, name='services-monitor')
)
