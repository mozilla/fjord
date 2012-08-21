from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'fjord.feedback.views',

    url(r'feedback', 'feedback_router', name='feedback_router'),
)
