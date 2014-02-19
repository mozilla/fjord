# This is your project's main settings file that can be committed to
# your repo. If you need to override a setting locally, use
# settings_local.py

from funfactory.settings_base import *


# Name of the top-level module where you put all your apps.  If you
# did not install Playdoh with the funfactory installer script you may
# need to edit this value. See the docs about installing from a clone.
PROJECT_MODULE = 'fjord'

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

# This is the list of languages that are active for non-DEV
# environments. Add languages here to allow users to see the site in
# that locale and additionally submit feedback in that locale.
PROD_LANGUAGES = [
    'ach',
    'af',
    'ak',
    'am-et',
    'an',
    'ar',
    'as',
    'ast',
    'az',
    'be',
    'bg',
    'bn-BD',
    'bn-IN',
    'br',
    'bs',
    'ca',
    'cs',
    'csb',
    'cy',
    'da',
    'dbg',
    'de',
    'de-AT',
    'de-CH',
    'de-DE',
    'dsb',
    'el',
    'en-AU',
    'en-CA',
    'en-GB',
    'en-NZ',
    'en-US',
    'en-ZA',
    'eo',
    'es',
    'es-AR',
    'es-CL',
    'es-ES',
    'es-MX',
    'et',
    'eu',
    'fa',
    'ff',
    'fi',
    'fj-FJ',
    'fr',
    'fur-IT',
    'fy',
    'fy-NL',
    'ga',
    'ga-IE',
    'gd',
    'gl',
    'gu-IN',
    'he',
    'hi',
    'hi-IN',
    'hr',
    'hsb',
    'hu',
    'hy-AM',
    'id',
    'is',
    'it',
    'ja',
    'ka',
    'kk',
    'km',
    'kn',
    'ko',
    'ku',
    'la',
    'lg',
    'lij',
    'lt',
    'lv',
    'mai',
    'mg',
    'mi',
    'mk',
    'ml',
    'mn',
    'mr',
    'ms',
    'my',
    'nb-NO',
    'ne-NP',
    'nl',
    'nn-NO',
    'nr',
    'nso',
    'oc',
    'or',
    'pa-IN',
    'pl',
    'pt',
    'pt-BR',
    'pt-PT',
    'rm',
    'ro',
    'ru',
    'rw',
    'sa',
    'sah',
    'si',
    'sk',
    'sl',
    'son',
    'sq',
    'sr',
    'sr-Latn',
    'ss',
    'st',
    'sv-SE',
    'sw',
    'ta',
    'ta-IN',
    'ta-LK',
    'te',
    'th',
    'tn',
    'tr',
    'ts',
    'tt-RU',
    'uk',
    'ur',
    've',
    'vi',
    'wo',
    'xh',
    'zh-CN',
    'zh-TW',
    'zu'
]

DEV_LANGUAGES = PROD_LANGUAGES

INSTALLED_APPS = get_apps(
    exclude=(
        'compressor',
    ),
    append=(
        # south has to come early, otherwise tests fail.
        'south',

        'django_browserid',
        'adminplus',
        'django.contrib.admin',
        'django_nose',
        'djcelery',
        'eadred',
        'jingo_minify',
        'dennis.django_dennis',

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
        'fjord.base.middleware.UserAgentMiddleware',
        'fjord.base.middleware.MobileQueryStringMiddleware',
        'fjord.base.middleware.MobileMiddleware',
        'django_statsd.middleware.GraphiteMiddleware',
        'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    ))

LOCALE_PATHS = (
    os.path.join(ROOT, PROJECT_MODULE, 'locale'),
)

SUPPORTED_NONLOCALES += (
    'robots.txt',
    'services',
    'api',
)

# Because Jinja2 is the default template loader, add any non-Jinja
# templated apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'adminplus',
    'registration',
    'browserid',
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
        'generic_feedback': (
            'css/lib/normalize.css',
            'css/lib/brick-1.0beta8.byob.min.css',
            # FIXME - This should become feedback.less and move out of
            # mobile/.
            'css/mobile/base.less',
            'css/generic_feedback.less',
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

        'mobile/base': (
            'css/lib/normalize.css',
            'css/mobile/base.less',
        ),
        'mobile/feedback': (
            'css/lib/normalize.css',
            'css/mobile/base.less',
            'css/mobile/feedback.less',
        ),
        'mobile/fxos_feedback': (
            'css/lib/normalize.css',
            'css/lib/brick-1.0beta8.byob.min.css',
            'css/mobile/base.less',
            'css/mobile/fxos_feedback.less',
        ),
        'mobile/thanks': (
            'css/lib/normalize.css',
            'css/mobile/base.less',
            'css/mobile/thanks.less',
        )
    },
    'js': {
        'base': (
            'js/lib/jquery.min.js',
            'browserid/browserid.js',
            'js/init.js',
            'js/ga.js',
        ),
        'feedback': (
            'js/lib/jquery.min.js',
            'js/init.js',
            'js/feedback.js',
            'js/ga.js',
        ),
        'generic_feedback': (
            'js/lib/jquery.min.js',
            'js/generic_feedback.js',
            'js/ga.js',
        ),
        'dashboard': (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/init.js',
            'js/lib/excanvas.js',
            'js/lib/jquery.flot.js',
            'js/lib/jquery.flot.time.js',
            'js/lib/jquery.flot.resize.js',
            'js/dashboard.js',
            'browserid/browserid.js',
            'js/ga.js',
        ),
        'mobile/base': (
            'js/lib/jquery.min.js',
            'js/ga.js',
        ),
        'mobile/feedback': (
            'js/lib/jquery.min.js',
            'js/mobile/feedback.js',
            'js/ga.js',
        ),
        'mobile/fxos_feedback': (
            'js/lib/jquery.min.js',
            'js/mobile/fxos_feedback.js',
            'js/ga.js',
        ),
    }
}
LESS_PREPROCESS = True
JINGO_MINIFY_USE_STATIC = True

LESS_BIN = 'lessc'
JAVA_BIN = 'java'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_browserid.auth.BrowserIDBackend',
]

BROWSERID_VERIFY_CLASS = 'fjord.base.browserid.FjordVerify'
BROWSERID_AUDIENCES = ['http://127.0.0.1:8000', 'http://localhost:8000']
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL_FAILURE = '/login-failure'

TEMPLATE_CONTEXT_PROCESSORS = get_template_context_processors(
    exclude=(),
    append=(
        'django_browserid.context_processors.browserid',
    ))

# Should robots.txt deny everything or disallow a calculated list of
# URLs we don't want to be crawled?  Default is false, disallow
# everything.  Also see
# http://www.google.com/support/webmasters/bin/answer.py?answer=93710
ENGAGE_ROBOTS = False

# Always generate a CSRF token for anonymous users.
ANON_ALWAYS = True

# Tells the extract script what files to look for L10n in and what
# function handles the extraction. The Tower library expects this.
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
#    # Make sure that this won't pull in strings from external
#    # libraries you may use.
#    ('media/js/**.js', 'javascript'),
# ]

# When set to True, this will cause a message to be displayed on all
# pages that this is not production.
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

# When True, objects that belong in the index will get automatically
# indexed and deindexed when created and destroyed.
ES_LIVE_INDEX = True

ES_TIMEOUT = 10

# Time in seconds before celery.exceptions.SoftTimeLimitExceeded is raised.
# The task can catch that and recover but should exit ASAP.
CELERYD_TASK_SOFT_TIME_LIMIT = 60 * 10

# Configuration for API views.
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': (
        'fjord.base.util.MeasuredAnonRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
    },
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}
