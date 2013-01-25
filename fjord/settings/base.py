# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py

from funfactory.settings_base import *

# Name of the top-level module where you put all your apps.
# If you did not install Playdoh with the funfactory installer script
# you may need to edit this value. See the docs about installing from a
# clone.
PROJECT_MODULE = 'fjord'

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

INSTALLED_APPS = get_apps(
    exclude=(
        'compressor',
    ),
    append=(
        # south has to come early, otherwise tests fail.
        'south',

        'adminplus',
        'django.contrib.admin',
        'django_nose',
        'djcelery',
        'eadred',
        'jingo_minify',
        'test_utils',

        'fjord.analytics',
        'fjord.base',
        'fjord.feedback',
        'fjord.search',
    ))

MIDDLEWARE_CLASSES = get_middleware(
    exclude=(
        # We do mobile detection ourselves.
        'mobility.middleware.DetectMobileMiddleware',
        'mobility.middleware.XMobileMiddleware',
    ),
    append=(
        'fjord.base.middleware.UseragentMiddleware',
        'fjord.base.middleware.MobileQueryStringOverrideMiddleware',
        'fjord.base.middleware.MobileMiddleware',
        'django_statsd.middleware.GraphiteMiddleware',
        'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    ))

LOCALE_PATHS = (
    os.path.join(ROOT, PROJECT_MODULE, 'locale'),
)

# Because Jinja2 is the default template loader, add any non-Jinja templated
# apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'adminplus',
    'registration',
]

MINIFY_BUNDLES = {
    'css': {
        'base': (
            'css/lib/normalize.css',
            'css/fjord.less',
        ),
        'feedback': (
            'css/lib/normalize.css',
            'css/feedback.less',
        ),
        'dashboard': (
            'css/ui-lightness/jquery-ui.css',
            'css/lib/normalize.css',
            'css/fjord.less',
            'css/dashboard.less',
        ),
        'stage': (
            'css/stage.less',
        ),
    },
    'js': {
        'base': (
            'js/lib/jquery.min.js',
            'js/init.js',
        ),
        'feedback': (
            'js/lib/jquery.min.js',
            'js/init.js',
            'js/feedback.js',
        ),
        'dashboard': (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/lib/excanvas.js',
            'js/lib/jquery.flot.js',
            'js/lib/jquery.flot.time.js',
            'js/lib/jquery.flot.resize.js',
            'js/init.js',
            'js/dashboard.js',
        ),
    }
}
LESS_PREPROCESS = True
JINGO_MINIFY_USE_STATIC = True

LESS_BIN = 'lessc'
JAVA_BIN = 'java'

# BrowserID configuration
AUTHENTICATION_BACKENDS = [
    'django_browserid.auth.BrowserIDBackend',
    'django.contrib.auth.backends.ModelBackend',
]

SITE_URL = 'http://127.0.0.1:8000'
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = 'examples.home'
LOGIN_REDIRECT_URL_FAILURE = 'examples.home'

TEMPLATE_CONTEXT_PROCESSORS = get_template_context_processors(
    exclude=(),
    append=(
        'django_browserid.context_processors.browserid_form',
    ))

# Should robots.txt deny everything or disallow a calculated list of URLs we
# don't want to be crawled?  Default is false, disallow everything.
# Also see http://www.google.com/support/webmasters/bin/answer.py?answer=93710
ENGAGE_ROBOTS = False

# Always generate a CSRF token for anonymous users.
ANON_ALWAYS = True

# Tells the extract script what files to look for L10n in and what function
# handles the extraction. The Tower library expects this.
DOMAIN_METHODS['messages'] = [
    ('%s/**.py' % PROJECT_MODULE,
        'tower.management.commands.extract.extract_tower_python'),
    ('%s/**/templates/**.html' % PROJECT_MODULE,
        'tower.management.commands.extract.extract_tower_template'),
    ('templates/**.html',
        'tower.management.commands.extract.extract_tower_template'),
]

# # Use this if you have localizable HTML files:
# DOMAIN_METHODS['lhtml'] = [
#    ('**/templates/**.lhtml',
#        'tower.management.commands.extract.extract_tower_template'),
# ]

# # Use this if you have localizable JS files:
# DOMAIN_METHODS['javascript'] = [
#    # Make sure that this won't pull in strings from external libraries you
#    # may use.
#    ('media/js/**.js', 'javascript'),
# ]

LOGGING = dict(loggers=dict(playdoh={'level': logging.DEBUG}))

# When set to True, this will cause a message to be displayed on all pages
# that this is not production.
SHOW_STAGE_NOTICE = False

# ElasticSearch settings.

# List of host urls for the ES hosts we should connect to.
ES_URLS = ['http://localhost:9200']

# Dict of mapping-type-name -> index-name to use. Input pretty much
# uses one index, so this should be some variation of:
# {'default': 'inputindex'}.
ES_INDEXES = {'default': 'inputindex'}

# Prefix for the index. This allows -dev and -stage to share the same
# ES cluster, but not bump into each other.
ES_INDEX_PREFIX = 'input'

# The indexing timeout to use. 30s is good.
ES_INDEXING_TIMEOUT = 30

# When True, objects that belong in the index will get automatically indexed
# and deindexed when created and destroyed.
ES_LIVE_INDEX = True
