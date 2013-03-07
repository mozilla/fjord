from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('fjord.base.views',
    url(r'^login-failure$', 'login_failure', name='login-failure'),

    url(r'^services/monitor$', 'monitor_view', name='services-monitor'),
    url(r'^services/throw-error$', 'throw_error', name='throw-error'),

    url(r'^about$', 'about_view', name='about-view')
)
