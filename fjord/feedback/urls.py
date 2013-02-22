from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('fjord.feedback.views',
    url(r'^feedback(?:/(?P<formname>[\w\._-]+))?/?$', 'feedback_router',
        name='feedback'),
    url(r'^thanks/$', 'thanks', name='thanks'),
)
