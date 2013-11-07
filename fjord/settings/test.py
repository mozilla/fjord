CELERY_ALWAYS_EAGER = True
SESSION_COOKIE_SECURE = False

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_PLUGINS = [
    'fjord.base.nose_plugins.SilenceSouth',
]
