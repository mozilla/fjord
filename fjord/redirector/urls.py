from django.conf.urls import patterns, url


urlpatterns = patterns(
    'fjord.redirector.views',

    url(r'^redirect/?$', 'redirect_view', name='redirect-view')
)
