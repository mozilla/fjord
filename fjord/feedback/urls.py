from django.conf.urls.defaults import patterns, url

from fjord.feedback import views


urlpatterns = patterns(
    'fjord.feedback.views',

    url(r'^feedback(?:/(?P<formname>[\w\._-]+))?/?$', 'feedback_router',
        name='feedback'),
    url(r'^thanks/$', 'thanks', name='thanks'),
    url(r'^downloadfirefox/$', 'download_firefox', name='download-firefox'),

    url(r'^happy/?$', 'happy_redirect', name='happy-redirect'),
    url(r'^sad/?$', 'sad_redirect', name='sad-redirect'),

    # API for posting feedback
    url(r'^api/v1/feedback/?$', views.PostFeedbackAPI.as_view(),
        name='api-post-feedback'),
)
