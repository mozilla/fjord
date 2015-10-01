from fjord.settings_utils import config


CELERY_ALWAYS_EAGER = True
SESSION_COOKIE_SECURE = False

CACHES = {
    'default': config(
        'CACHE_URL', default='locmem://', type_='cache_url'
    )
}

SUGGEST_PROVIDERS = []

PIPELINE_ENABLED = True
