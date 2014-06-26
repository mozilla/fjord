from django.conf.urls import patterns, url

from fjord.feedback import api_views


urlpatterns = patterns(
    'fjord.feedback.views',

    # feedback/%PRODUCT%/%VERSION%/%CHANNEL%
    url(r'^feedback'
        r'(?:/(?P<product>[^/]+)'
        r'(?:/(?P<version>[^/]+)'
        r'(?:/(?P<channel>[^/]+))?)?)?'
        r'/?$',
        'feedback_router', name='feedback'),

    # feedback-dev/%PRODUCT%/%VERSION%/%CHANNEL% FOR DEVELOPMENT
    url(r'^feedback-dev'
        r'(?:/(?P<product>[^/]+)'
        r'(?:/(?P<version>[^/]+)'
        r'(?:/(?P<channel>[^/]+))?)?)?'
        r'/?$',
        'feedback_router_dev', name='feedback_dev'),

    url(r'^thanks/?$', 'thanks', name='thanks'),
    url(r'^downloadfirefox/?$', 'download_firefox', name='download-firefox'),

    # These are redirects for backwards compatibility with old urls
    # used for Firefox feedback
    url(r'^happy/?$', 'happy_redirect', name='happy-redirect'),
    url(r'^sad/?$', 'sad_redirect', name='sad-redirect'),

    # API for posting feedback
    # Note: If we change the version number here, we also have to change it
    # in the ResponseSerializer.
    url(r'^api/v1/feedback/?$',
        api_views.feedback_as_view(), name='feedback-api'),
)
