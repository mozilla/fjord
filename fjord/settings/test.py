from fjord.settings_utils import config


DEBUG = TEMPLATE_DEBUG = True
CELERY_ALWAYS_EAGER = True
SESSION_COOKIE_SECURE = False

# This sets some nose flags otherwise testing is very noisy. Comment
# these out if you need the information they're quelling.
#
# See http://fjord.readthedocs.org/en/latest/testing.html
NOSE_ARGS = [
    '-s',                       # Don't ask any questions
    '--nocapture',              # Don't capture stdout
    '--logging-clear-handlers'  # Clear all other logging handlers
]

CACHES = {
    'default': config(
        'CACHE_URL', default='locmem://', type_='cache_url'
    )
}
