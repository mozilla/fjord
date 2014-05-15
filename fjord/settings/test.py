DEBUG = TEMPLATE_DEBUG = True
CELERY_ALWAYS_EAGER = True
SESSION_COOKIE_SECURE = False

# FIXME: Have to have this as True (the default) for now because we
# depend on data migrations. That causes problems with
# LiveServerTestCase, though.
# SOUTH_TESTS_MIGRATE = False

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_PLUGINS = [
    'fjord.base.nose_plugins.SilenceSouth',
]
