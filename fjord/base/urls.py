from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to


urlpatterns = patterns('fjord.base.views',
    url(r'^$', 'home_view', name='home_view'),

    url(r'^services/monitor$', 'monitor_view', name='services-monitor'),
    url(r'^services/throw-error$', 'throw_error', name='throw-error'),

    url(r'^about$', redirect_to, {'url': 'stub'}, name='about'),
)
