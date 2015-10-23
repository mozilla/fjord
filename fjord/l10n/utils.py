import re

from babel.messages.extract import DEFAULT_KEYWORDS as BABEL_KEYWORDS


def generate_keywords():
    """Generates gettext keywords list"""
    keywords = set(BABEL_KEYWORDS.keys())
    keywords.add('_lazy')
    # FIXME: Add other keywords here
    return list(keywords)


_COLLAPSE_RE = re.compile(r'\s+', re.UNICODE)


def collapse_whitespace(message):
    """Collapses consecutive whitespace into a single space"""
    return _COLLAPSE_RE.sub(' ', message).strip()
