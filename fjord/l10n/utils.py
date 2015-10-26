from babel.messages.extract import DEFAULT_KEYWORDS as BABEL_KEYWORDS


def generate_keywords():
    """Generates gettext keywords list"""
    keywords = set(BABEL_KEYWORDS.keys())
    keywords.add('_lazy')
    # FIXME: Add other keywords here
    return list(keywords)


def collapse_whitespace(message):
    """Collapses consecutive whitespace into a single space"""
    return u' '.join(map(lambda s: s.strip(), message.strip().splitlines()))
