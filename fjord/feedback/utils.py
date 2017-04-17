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
