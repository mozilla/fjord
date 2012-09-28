from datetime import datetime


def smart_truncate(content, length=100, suffix='...'):
    """Truncate text at space before length bound.

    :arg content: string to truncate
    :arg length: length to truncate at
    :arg suffix: text to append to truncated content

    :returns: string

    Example:

    >>> smart_truncate('abcde fghij', length=8)
    'abcde...'
    >>> smart_truncate('abcde fghij', length=100)
    'abcde fghij'

    """
    if len(content) <= length:
        return content
    else:
        return content[:length].rsplit(' ', 1)[0] + suffix


def smart_int(s, fallback=0):
    """Convert a string to int, with fallback for invalid strings or types."""
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return fallback


def smart_datetime(s, format='%Y-%m-%d', fallback=None):
    """Convert a string to a datetime, with a fallback for invalid input.

    Note that this won't take ``datetime``s as input, only strings. It is
    different than ``smart_int`` in this way.

    :arg s: The string to convert to a date.
    :arg format: Format to use to parse the string into a date. Default: ``'%Y-%m-%d'``.
    :arg fallback: Value to use in case of an error. Default: ``None``.

    """
    try:
        return datetime.strptime(s, format)
    except (ValueError, TypeError):
        return fallback

