from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    'fjord.base.views',

    url(r'^$', 'home_view', name='home_view'),
    url(r'^about$', 'home_view', name='about'),
    url(r'^search$', 'home_view', name='search'),
    url(r'^themes$', 'home_view', name='themes'),
    url(r'^issues$', 'home_view', name='website_issues'),
)
