# This is your project's main settings file that can be committed to
# your repo. If you need to override a setting locally, use
# settings_local.py

import logging
import os
import socket

from django.utils.functional import lazy


ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        '..'
    ))


def path(*dirs):
    return os.path.join(ROOT, *dirs)


# Name of the top-level module where you put all your apps.
PROJECT_MODULE = 'fjord'

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

ADMINS = ()
MANAGERS = ADMINS
DEV = False

DATABASES = {}  # See settings_local.

SLAVE_DATABASES = []

DATABASE_ROUTERS = ('multidb.PinningMasterSlaveRouter',)

# Site ID is used by Django's Sites framework.
SITE_ID = 1

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
TEXT_DOMAIN = 'messages'
STANDALONE_DOMAINS = [TEXT_DOMAIN, 'javascript']
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
    'tower',  # for ./manage.py extract (L10n)
    'cronjobs',  # for ./manage.py cron * cmd line tasks
    'django_browserid',

    # Django contrib apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    # Third-party apps, patches, fixes
    'commonware.response.cookies',
    'djcelery',
    'django_nose',
    'session_csrf',
    'waffle',

    # L10n
    'product_details',

    # south has to come early, otherwise tests fail.
    'south',

    'adminplus',

    # This has to come before Grappelli since it contains fixed HTML
    # for displaying django-adminplus custom views in the Grappelli
    # index.html page.
    'fjord.grappellioverride',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.messages',
    'django_extensions',
    'django_nose',
    'djcelery',
    'eadred',
    'jingo_minify',
    'dennis.django_dennis',

    'fjord.analytics',
    'fjord.base',
    'fjord.events',
    'fjord.feedback',
    'fjord.flags',
    'fjord.heartbeat',
    'fjord.journal',
    'fjord.search',
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
    os.path.join(ROOT, PROJECT_MODULE, 'locale'),
)

SUPPORTED_NONLOCALES = [
    'admin',
    'api',
    'browserid',
    'media',
    'robots.txt',
    'contribute.json',
    'services',
    'static',
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
            'tower.template.i18n',
            'jinja2.ext.do',
            'jinja2.ext.with_',
            'jinja2.ext.loopcontrols'
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

MINIFY_BUNDLES = {
    'css': {
        'base': (
            'css/lib/normalize.css',
            'css/fjord.less',
        ),
        'dashboard': (
            'css/ui-lightness-jquery-ui.css',
            'css/lib/normalize.css',
            'css/fjord.less',
            'css/dashboard.less',
        ),
        'monitor': (
            'css/ui-lightness-jquery-ui.css',
            'css/lib/normalize.css',
            'css/fjord.less',
            'css/monitor.less',
        ),
        'stage': (
            'css/stage.less',
        ),
        'mobile/base': (
            'css/lib/normalize.css',
            'css/mobile/base.less',
        ),
        'generic_feedback': (
            'css/lib/normalize.css',
            'css/generic_feedback.less',
        ),
        'thanks': (
            'css/lib/normalize.css',
            'css/thanks.less',
        ),
        'fxos_feedback': (
            'css/lib/normalize.css',
            'css/lib/brick-1.0.0.byob.min.css',
            'css/feedback_base.less',
            'css/fxos_feedback.less',
        ),
    },
    'js': {
        'base': (
            'js/lib/jquery.min.js',
            'browserid/browserid.js',
            'js/init.js',
            'js/ga.js',
        ),
        'dashboard': (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/init.js',
            'js/fjord_utils.js',
            'js/lib/excanvas.js',
            'js/lib/jquery.flot.js',
            'js/lib/jquery.flot.time.js',
            'js/lib/jquery.flot.resize.js',
            'js/dashboard.js',
            'browserid/browserid.js',
            'js/ga.js',
        ),
        'hourlydashboard': (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/init.js',
            'js/fjord_utils.js',
            'js/lib/excanvas.js',
            'js/lib/jquery.flot.js',
            'js/lib/jquery.flot.time.js',
            'js/lib/jquery.flot.resize.js',
            'js/hourly_dashboard.js',
            'browserid/browserid.js',
            'js/ga.js',
        ),
        'productdashboard': (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/init.js',
            'js/fjord_utils.js',
            'js/lib/excanvas.js',
            'js/lib/jquery.flot.js',
            'js/lib/jquery.flot.time.js',
            'js/lib/jquery.flot.resize.js',
            'js/product_dashboard.js',
            'browserid/browserid.js',
            'js/ga.js',
        ),
        'productdashboardfirefox': (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/init.js',
            'js/fjord_utils.js',
            'js/lib/excanvas.js',
            'js/lib/jquery.flot.js',
            'js/lib/jquery.flot.time.js',
            'js/lib/jquery.flot.resize.js',
            'js/product_dashboard_firefox.js',
            'browserid/browserid.js',
            'js/ga.js',
        ),
        'singlecard': (
            'js/lib/jquery.min.js',
            'js/ga.js',
        ),
        'generic_feedback': (
            'js/lib/jquery.min.js',
            'js/fjord_utils.js',
            'js/common_feedback.js',
            'js/generic_feedback.js',
            'js/ga.js',
        ),
        'generic_feedback_dev': (
            'js/lib/jquery.min.js',
            'js/fjord_utils.js',
            'js/remote.js',
            'js/common_feedback.js',
            'js/generic_feedback_dev.js',
            'js/ga.js',
        ),
        'thanks': (
            'js/lib/jquery.min.js',
            'js/init.js',
            'js/ga.js',
        ),
        'fxos_feedback': (
            'js/lib/jquery.min.js',
            'js/fjord_utils.js',
            'js/common_feedback.js',
            'js/fxos_feedback.js',
            'js/ga.js',
        ),
    }
}
LESS_PREPROCESS = True
JINGO_MINIFY_USE_STATIC = True

LESS_BIN = 'lessc'
JAVA_BIN = 'java'

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
    'django_browserid.context_processors.browserid',
)

TEMPLATE_DIRS = (
    path('templates'),
)

# Should robots.txt deny everything or disallow a calculated list of
# URLs we don't want to be crawled?  Default is false, disallow
# everything.  Also see
# http://www.google.com/support/webmasters/bin/answer.py?answer=93710
ENGAGE_ROBOTS = False

# Always generate a CSRF token for anonymous users.
ANON_ALWAYS = True

# CSRF error page
CSRF_FAILURE_VIEW = 'fjord.base.views.csrf_failure'

# Tells the extract script what files to look for L10n in and what
# function handles the extraction. The Tower library expects this.
DOMAIN_METHODS = {
    'messages': [
        ('%s/**.py' % PROJECT_MODULE,
         'tower.management.commands.extract.extract_tower_python'),
        ('%s/**/templates/**.html' % PROJECT_MODULE,
         'tower.management.commands.extract.extract_tower_template'),
        ('templates/**.html',
         'tower.management.commands.extract.extract_tower_template'),
    ]
}


# When set to True, this will cause a message to be displayed on all
# pages that this is not production.
SHOW_STAGE_NOTICE = False

# Gengo settings
GENGO_PUBLIC_KEY = None
GENGO_PRIVATE_KEY = None
GENGO_USE_SANDBOX = True
GENGO_ACCOUNT_BALANCE_THRESHOLD = 100.0

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder'
)

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

# For absolute urls
try:
    DOMAIN = socket.gethostname()
except socket.error:
    DOMAIN = 'localhost'
PROTOCOL = "http://"
PORT = 80

## Logging
LOG_LEVEL = logging.INFO
HAS_SYSLOG = True
SYSLOG_TAG = "http_app_playdoh"  # Change this after you fork.
LOGGING_CONFIG = None
LOGGING = {}

try:
    len(LOGGING)
except AttributeError:
    LOGGING = {}

LOGGING.setdefault('loggers', {})['elasticsearch'] = {
    'level': logging.ERROR
}
