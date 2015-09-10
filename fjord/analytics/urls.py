from django.conf.urls import patterns, url

from fjord.analytics.analyzer_views import ProductsUpdateView


urlpatterns = patterns(
    'fjord.analytics.views',

    # This covers / and /dashboard
    url(r'^(?:dashboard/?)?$', 'dashboard', name='dashboard'),

    # Show a specific response
    url(r'^dashboard/response/(?P<responseid>\d+)/?$',
        'response_view', name='response_view'),

    # Translate a specific response
    url(r'^dashboard/translate/(?P<responseid>\d+)/?$',
        'spot_translate', name='spot_translate'),
)

# These are analyzer-group only views.
urlpatterns += patterns(
    'fjord.analytics.analyzer_views',

    # Analytics dashboard
    url(r'^analytics/?$', 'analytics_dashboard',
        name='analytics_dashboard'),
    url(r'^analytics/products/?$', ProductsUpdateView.as_view(),
        name='analytics_products'),
    url(r'^analytics/search/?$', 'analytics_search',
        name='analytics_search'),
)
