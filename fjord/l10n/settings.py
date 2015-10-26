from fjord.l10n.utils import generate_keywords


# Name for .pot file--should be 'django'
TEXT_DOMAIN = 'django'

# Keywords indicating gettext calls
KEYWORDS = generate_keywords()

# By default, all the domains you speficy will be merged into one big
# messages.po file. If you want to separate a domain from the main .po file,
# specify it in this list. Make sure to include TEXT_DOMAIN in this list, even
# if you have other .po files you're generating
STANDALONE_DOMAINS = [TEXT_DOMAIN]

# Prefixes that indicate a comment tag intended for localizers
COMMENT_TAGS = ['L10n:', 'L10N:', 'l10n:', 'l10N:']

# Tells the extract script what files to look for L10n in and what
# function handles the extraction.
# Map of domain to list of (match, extractor)
DOMAIN_METHODS = None

# The root directory of this project to extract strings from
ROOT = None

# If you set this, we'll use it. Otherwise we assume you're using
# django-jinja and we'll pick up the first template setting
JINJA2_CONFIG = None


def get_setting(key):
    from django.conf import settings
    return settings.TOWER.get(key, globals()[key])
