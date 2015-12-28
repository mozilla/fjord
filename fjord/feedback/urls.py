from django.conf.urls import patterns, url

from fjord.feedback import api_views


urlpatterns = patterns(
    'fjord.feedback.views',

    # feedback/
    url(r'^feedback/?$', 'picker_view', name='picker'),

    # feedback/%PRODUCT%/%VERSION%/%CHANNEL%
    url(r'^feedback'
        r'/(?P<product_slug>[^/]+)'
        r'(?:/(?P<version>[^/]+)'
        r'(?:/(?P<channel>[^/]+))?)?'
        r'/?$',
        'feedback_router', name='feedback'),

    url(r'^thanks/?$', 'thanks_view', name='thanks'),

    # These are redirects for backwards compatibility with old urls
    # used for Firefox feedback
    url(r'^happy/?$', 'happy_redirect', name='happy-redirect'),
    url(r'^sad/?$', 'sad_redirect', name='sad-redirect'),

    url(r'^api/v1/feedback/histogram/?$',
        api_views.FeedbackHistogramAPI.as_view(),
        name='feedback-histogram-api'),

    # API for getting/posting feedback
    # Note: If we change the version number here, we also have to change it
    # in the ResponseSerializer.
    url(r'^api/v1/feedback/?$',
        api_views.feedback_as_view(), name='feedback-api'),
)
