from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to


urlpatterns = patterns('fjord.search.views',
    url(r'^search$', redirect_to, {'url': 'stub'}, name='search'),
)
