from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    'fjord.analytics.views',

    # This covers / and /dashboard
    url(r'^(?:dashboard)?$', 'dashboard', name='dashboard'),

    # Show a specific response
    url(r'^dashboard/response/(?P<responseid>\d+)/?$',
        'response_view', name='response_view'),

    # Analyzers dashboard
    url(r'^adashboard/?$', 'analytics_dashboard', name='analytics_dashboard'),

    # Spam dashboard
    url(r'^sdashboard/?$', 'spam_dashboard', name='spam_dashboard')
)
