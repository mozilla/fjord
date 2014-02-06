from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    'fjord.analytics.views',

    # This covers / and /dashboard
    url(r'^(?:dashboard/?)?$', 'dashboard', name='dashboard'),

    # Show a specific response
    url(r'^dashboard/response/(?P<responseid>\d+)/?$',
        'response_view', name='response_view'),

)

# These are analyzer-group only views.
urlpatterns += patterns(
    'fjord.analytics.analyzer_views',

    # Analytics dashboard
    url(r'^analytics/?$', 'analytics_dashboard',
        name='analytics_dashboard'),
    url(r'^analytics/occurrences/?$', 'analytics_occurrences',
        name='analytics_occurrences'),
    url(r'^analytics/products/?$', 'analytics_products',
        name='analytics_products'),

    url(r'^analytics/duplicates/?$', 'analytics_duplicates', name='analytics_duplicates'),
)
