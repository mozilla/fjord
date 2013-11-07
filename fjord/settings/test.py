CELERY_ALWAYS_EAGER = True

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_PLUGINS = [
    'fjord.base.nose_plugins.SilenceSouth',
]
