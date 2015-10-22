import re


_COLLAPSE_RE = re.compile(r'\s+', re.UNICODE)


def collapse_whitespace(message):
    """Collapses consecutive whitespace into a single space"""
    return _COLLAPSE_RE.sub(' ', message).strip()
