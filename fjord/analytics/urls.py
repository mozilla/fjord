from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('fjord.analytics.views',

    url(r'^(?:dashboard)?$', 'dashboard', name='dashboard'),
)
