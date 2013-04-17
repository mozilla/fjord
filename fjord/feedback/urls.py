from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    'fjord.feedback.views',

    url(r'^feedback(?:/(?P<formname>[\w\._-]+))?/?$', 'feedback_router',
        name='feedback'),
    url(r'^thanks/$', 'thanks', name='thanks'),
    url(r'^downloadfirefox/$', 'download_firefox', name='download-firefox'),

    url(r'^happy/?$', 'happy_redirect', name='happy-redirect'),
    url(r'^sad/?$', 'sad_redirect', name='sad-redirect'),
)
