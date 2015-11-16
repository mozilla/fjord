import re
# unicodedata2 is the unicodedata backport to Python 2
try:
    import unicodedata2 as unicodedata
except ImportError:
    import unicodedata

import urlparse


def clean_url(url):
    """Takes a user-supplied url and cleans bits out

    This removes:

    1. nixes any non http/https/chrome/about urls
    2. port numbers
    3. query string variables
    4. hashes

    """
    if not url:
        return url

    # Don't mess with about: urls.
    if url.startswith('about:'):
        return url

    parsed = urlparse.urlparse(url)

    if parsed.scheme not in ('http', 'https', 'chrome'):
        return u''

    # Rebuild url to drop querystrings, hashes, etc
    new_url = (parsed.scheme, parsed.hostname, parsed.path, None, None, None)

    return urlparse.urlunparse(new_url)


POSSIBLE_EMOJIS_RE = re.compile(u'[\U00010000-\U0010ffff]')


def convert_emoji(text):
    """Takes unicode text and converts emoji characters

    Emoji break MySQL, so we convert them into ascii.

    """
    # convert to unicodedata.name()
    def _convert(match_char):
        c = match_char.group(0)
        try:
            return unicodedata.name(c)
        except ValueError:
            # Throws a ValueError if the name doesn't exist.
            return ''
    return POSSIBLE_EMOJIS_RE.sub(_convert, text)
