# This is your project's main settings file that can be committed to
# your repo. If you need to override a setting locally, use
# settings_local.py

import logging
import os

from django.utils.functional import lazy

from fjord.settings_utils import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BASE_DIR)


def path(*dirs):
    return os.path.join(ROOT, *dirs)


# Name of the top-level module where you put all your apps.
PROJECT_MODULE = 'fjord'

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

ADMINS = ()
DEV = False

DATABASES = {'default': config('DATABASE_URL', type_='database_url')}

SLAVE_DATABASES = []

DATABASE_ROUTERS = ('multidb.PinningMasterSlaveRouter',)

CACHES = {'default': config('CACHE_URL', type_='cache_url')}

# Need this because the settings file on -stage and -prod specify
# MANAGERS so it fails the check.
TEST_RUNNER = 'fake.test.runner'

## Internationalization.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Gettext text domain
TEXT_DOMAIN = 'django'
STANDALONE_DOMAINS = [TEXT_DOMAIN]
TOWER_KEYWORDS = {'_lazy': None}
TOWER_ADD_HEADERS = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

# Tells the product_details module where to find our local JSON files.
# This ultimately controls how LANGUAGES are constructed.
PROD_DETAILS_DIR = path('lib/product_details_json')

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

DEV_LANGUAGES = PROD_LANGUAGES + ['xx']


def lazy_lang_url_map():
    from django.conf import settings
    langs = settings.DEV_LANGUAGES if settings.DEV else settings.PROD_LANGUAGES
    return dict([(i.lower(), i) for i in langs])

LANGUAGE_URL_MAP = lazy(lazy_lang_url_map, dict)()

# Override Django's built-in with our native names
def lazy_langs():
    from django.conf import settings
    from product_details import product_details
    langs = DEV_LANGUAGES if settings.DEV else settings.PROD_LANGUAGES
    return dict([(lang.lower(), product_details.languages[lang]['native'])
                 for lang in langs if lang in product_details.languages])

LANGUAGES = lazy(lazy_langs, dict)()

INSTALLED_APPS = (
    # Local apps
    'cronjobs',  # for ./manage.py cron * cmd line tasks
    'django_browserid',

    # Django contrib apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    # Third-party apps, patches, fixes
    'commonware.response.cookies',
    'session_csrf',
    'waffle',

    'product_details',

    'adminplus',

    # This has to come before Grappelli since it contains fixed HTML
    # for displaying django-adminplus custom views in the Grappelli
    # index.html page.
    'fjord.grappellioverride',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.messages',
    'django_extensions',
    'eadred',
    'pipeline',
    'dennis.django_dennis',

    'fjord.alerts',
    'fjord.analytics',
    'fjord.api_auth',
    'fjord.base',
    'fjord.events',
    'fjord.feedback',
    'fjord.flags',
    'fjord.heartbeat',
    'fjord.journal',
    'fjord.search',
    'fjord.suggest',
    'fjord.suggest.providers.trigger',
    'fjord.redirector',
    'fjord.translations',
)

MIDDLEWARE_CLASSES = (
    'fjord.base.middleware.LocaleURLMiddleware',

    'multidb.middleware.PinningRouterMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Must be after auth middleware.
    'session_csrf.CsrfMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'commonware.middleware.FrameOptionsHeader',
    'waffle.middleware.WaffleMiddleware',

    'fjord.base.middleware.UserAgentMiddleware',
    'fjord.base.middleware.MobileQueryStringMiddleware',
    'fjord.base.middleware.MobileMiddleware',

    'django_statsd.middleware.GraphiteMiddleware',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
)

LOCALE_PATHS = (
    os.path.join(ROOT, 'locale'),
)

SUPPORTED_NONLOCALES = [
    'favicon.ico',
    'admin',
    'api',
    'browserid',
    'media',
    'robots.txt',
    'contribute.json',
    'redirect',  # from fjord.redirector
    'services',  # from fjord.base
    'static',
]

SUGGEST_PROVIDERS = [
    'fjord.suggest.providers.sumo.SUMOSuggest',
    'fjord.suggest.providers.trigger.provider.TriggerSuggester',
]
REDIRECTOR_PROVIDERS = [
    'fjord.suggest.providers.sumo.SUMOSuggestRedirector',
    'fjord.suggest.providers.trigger.provider.TriggerRedirector',
]

## Media and templates.

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = path('static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

def JINJA_CONFIG():
    config = {
        'extensions': [
            'fjord.base.l10n.MozInternationalizationExtension',
            'jinja2.ext.do',
            'jinja2.ext.with_',
            'jinja2.ext.loopcontrols',
            'pipeline.templatetags.ext.PipelineExtension',
        ],
        'finalize': lambda x: x if x is not None else ''
    }
    return config

# Because Jinja2 is the default template loader, add any non-Jinja
# templated apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'adminplus',
    'grappelli',
    'registration',
    'browserid',
]

# Django Pipeline
PIPELINE_CSS = {
    'base': {
        'source_filenames': (
            'css/lib/normalize.css',
            'css/fjord.less',
        ),
        'output_filename': 'base.css'
    },
    'dashboard': {
        'source_filenames': (
            'css/ui-lightness-jquery-ui.css',
            'css/lib/normalize.css',
            'css/fjord.less',
            'css/dashboard.less',
        ),
        'output_filename': 'dashboard.css'
    },
    'monitor': {
        'source_filenames': (
            'css/ui-lightness-jquery-ui.css',
            'css/lib/normalize.css',
            'css/fjord.less',
            'css/monitor.less',
        ),
        'output_filename': 'monitor.css'
    },
    'mobile-base': {
        'source_filenames': (
            'css/lib/normalize.css',
            'css/mobile/base.less',
        ),
        'output_filename': 'mobile-base.css'
    },
    'feedback': {
        'source_filenames': (
            'css/lib/normalize.css',
            'css/feedback.less',
        ),
        'output_filename': 'feedback.css'
    },
}

PIPELINE_JS = {
    'base': {
        'source_filenames': (
            'js/lib/jquery.min.js',
            'browserid/api.js',
            'browserid/browserid.js',
            'js/init.js',
            'js/ga.js',
        ),
        'output_filename': 'base.js'
    },
    'dashboard': {
        'source_filenames': (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/init.js',
            'js/fjord_utils.js',
            'js/lib/excanvas.js',
            'js/lib/jquery.flot.js',
            'js/lib/jquery.flot.time.js',
            'js/lib/jquery.flot.resize.js',
            'js/dashboard.js',
            'browserid/api.js',
            'browserid/browserid.js',
            'js/ga.js',
        ),
        'output_filename': 'dashboard.js'
    },
    'singlecard': {
        'source_filenames': (
            'js/lib/jquery.min.js',
            'js/ga.js',
        ),
        'output_filename': 'singlecard.js'
    },
    'generic_feedback': {
        'source_filenames': (
            'js/lib/jquery.min.js',
            'js/fjord_utils.js',
            'js/remote.js',
            'js/cards.js',
            'js/common_feedback.js',
            'js/generic_feedback.js',
            'js/ga.js',
        ),
        'output_filename': 'generic_feedback.js'
    },
    'fxos_feedback': {
        'source_filenames': (
            'js/lib/jquery.min.js',
            'js/fjord_utils.js',
            'js/cards.js',
            'js/common_feedback.js',
            'js/fxos_feedback.js',
            'js/ga.js',
        ),
        'output_filename': 'fxos_feedback.js'
    },
}

PIPELINE_COMPILERS = (
    'pipeline.compilers.less.LessCompiler',
)

PIPELINE_DISABLE_WRAPPER = True

PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.uglifyjs.UglifyJSCompressor'
PIPELINE_UGLIFYJS_BINARY = path('node_modules/.bin/uglifyjs')
PIPELINE_UGLIFYJS_ARGUMENTS = '-r "\$super"'

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.cssmin.CSSMinCompressor'
PIPELINE_CSSMIN_BINARY = path('node_modules/.bin/cssmin')

PIPELINE_LESS_BINARY = path('node_modules/.bin/lessc')

# Sessions
#
# By default, be at least somewhat secure with our session cookies.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_browserid.auth.BrowserIDBackend',
]

## Auth
# The first hasher in this list will be used for new passwords.
# Any other hasher in the list can be used for existing passwords.
# Playdoh ships with Bcrypt+HMAC by default because it's the most secure.
# To use bcrypt, fill in a secret HMAC key in your local settings.
BASE_PASSWORD_HASHERS = (
    'django_sha2.hashers.BcryptHMACCombinedPasswordVerifier',
    'django_sha2.hashers.SHA512PasswordHasher',
    'django_sha2.hashers.SHA256PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
)
HMAC_KEYS = {  # for bcrypt only
    #'2012-06-06': 'cheesecake',
}

from django_sha2 import get_password_hashers
PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)

BROWSERID_VERIFY_CLASS = 'fjord.base.browserid.FjordVerify'
BROWSERID_AUDIENCES = ['http://127.0.0.1:8000', 'http://localhost:8000']
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL_FAILURE = '/login-failure'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'jingo.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'session_csrf.context_processor',
    'django.contrib.messages.context_processors.messages',
    'fjord.base.context_processors.i18n',
    'fjord.base.context_processors.globals',
)

TEMPLATE_DIRS = (
    path('templates'),
)

# Always generate a CSRF token for anonymous users.
ANON_ALWAYS = True

# CSRF error page
CSRF_FAILURE_VIEW = 'fjord.base.views.csrf_failure'

# Tells the extract script what files to look for L10n in and what
# function handles the extraction.
DOMAIN_METHODS = {
    'django': [
        ('%s/**.py' % PROJECT_MODULE,
         'fjord.base.l10n.extract_tower_python'),
        ('%s/**/templates/**.html' % PROJECT_MODULE,
         'fjord.base.l10n.extract_tower_template'),
        ('templates/**.html',
         'fjord.base.l10n.extract_tower_template'),
    ]
}

WSGI_APPLICATION = 'fjord.wsgi.application'

# Gengo settings
GENGO_PUBLIC_KEY = None
GENGO_PRIVATE_KEY = None
GENGO_USE_SANDBOX = True
GENGO_ACCOUNT_BALANCE_THRESHOLD = 100.0

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# ElasticSearch settings.

# List of host urls for the ES hosts we should connect to.
ES_URLS = config(
    'ES_URLS', default='http://localhost:9200', type_='list_of_str'
)

# Dict of doctype name -> index-name to use. Input pretty much
# uses one index, so this should be some variation of:
# {'default': 'inputindex'}.
ES_INDEXES = {'default': 'inputindex'}

# Prefix for the index. This allows -dev and -stage to share the same
# ES cluster, but not bump into each other.
ES_INDEX_PREFIX = config('ES_INDEX_PREFIX', default='input', type_='str')

# When True, objects that belong in the index will get automatically
# indexed and deindexed when created and destroyed.
ES_LIVE_INDEX = True

ES_TIMEOUT = 10

## Celery

# True says to simulate background tasks without actually using celeryd.
# Good for local development in case celeryd is not running.
CELERY_ALWAYS_EAGER = True

BROKER_CONNECTION_TIMEOUT = 0.1
CELERY_RESULT_BACKEND = 'amqp'
CELERY_IGNORE_RESULT = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Time in seconds before celery.exceptions.SoftTimeLimitExceeded is raised.
# The task can catch that and recover but should exit ASAP.
CELERYD_TASK_SOFT_TIME_LIMIT = 60 * 10

# Configuration for API views.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (),
    # We don't use throttle settings. Specify throttling in the views.
    'DEFAULT_THROTTLE_CLASSES': (),
    'DEFAULT_THROTTLE_RATES': {},
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

# Grappelli settings
GRAPPELLI_ADMIN_TITLE = 'Input admin and diabolical dashboard'

# Waffle settings
# Always allow for override via querystring
WAFFLE_OVERRIDE = True

## Logging
LOG_LEVEL = logging.INFO
HAS_SYSLOG = True
SYSLOG_TAG = 'http_app_playdoh'  # Change this after you fork.
LOGGING_CONFIG = None
LOGGING = {}

LOGGING.setdefault('loggers', {})['elasticsearch'] = {
    'level': logging.ERROR
}
