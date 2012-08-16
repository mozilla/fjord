from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    'fjord.base.views',

    url(r'^$', 'home_view', name='home_view'),
)
