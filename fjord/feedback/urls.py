from django.conf.urls.defaults import patterns, url

from fjord.feedback import views


urlpatterns = patterns(
    'fjord.feedback.views',

    # feedback/%PRODUCT%/%VERSION%/%CHANNEL%
    url(r'^feedback'
        r'(?:/(?P<product>[^/]+)'
        r'(?:/(?P<version>[^/]+)'
        r'(?:/(?P<channel>[^/]+))?)?)?'
        r'/?$',
        'feedback_router', name='feedback'),

    url(r'^thanks/$', 'thanks', name='thanks'),
    url(r'^downloadfirefox/$', 'download_firefox', name='download-firefox'),

    # These are redirects for backwards compatibility with old urls
    # used for Firefox feedback
    url(r'^happy/?$', 'happy_redirect', name='happy-redirect'),
    url(r'^sad/?$', 'sad_redirect', name='sad-redirect'),

    # API for posting feedback
    url(r'^api/v1/feedback/?$',
        views.PostFeedbackAPI.as_view(), name='api-post-feedback'),
)
