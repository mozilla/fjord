import threading

import tldextract


# Cache of thread-local TLDExtract objects
_cached_tldextract = threading.local()


def get_domain(url):
    """Returns the domain for a given url.

    This nicely deals with about: and chrome:// urls, too.

    >>> get_domain('http://foo.example.com/some-path')
    'example.com'
    >>> get_domain('http://foo.example.com.br')
    'example.com.br'
    >>> get_domain('about:home')
    ''
    >>> get_domain('127.0.0.1')
    ''
    >>> get_domain('chrome://whatever')
    ''
    >>> get_domain('ftp://blah@example.com')
    ''
    >>> get_domain('')
    ''

    """
    if not url:
        return u''

    if isinstance(url, unicode):
        url = url.encode('utf-8')

    # If there's a : in the url, then it either separates the scheme
    # from the host or the host from the port. If there's a scheme we
    # want to limit it to http or https.
    if ':' in url:
        scheme, host = url.split(':', 1)
        # If there's a . in the scheme, then there wasn't a scheme
        # and the : is delimiting the host from the port
        if '.' not in scheme and scheme not in ('http', 'https'):
            return u''

    # Get a thread-local extractor if there is one. If not, create it.
    extractor = getattr(_cached_tldextract, 'extractor', None)
    if extractor is None:
        # FIXME - This uses the tld set included with tldextract which
        # will age over time. We should fix this so that we get a new
        # file on deployment and use that file.
        extractor = tldextract.TLDExtract(
            suffix_list_url=None,  # disable fetching the file via http
        )
        _cached_tldextract.extractor = extractor

    res = extractor(url)

    # If there's no tld, then this is probably an ip address or
    # localhost. Also ignore .mil and .arpa addresses.
    if res.suffix in ('', 'mil', 'in-addr.arpa'):
        return u''

    # Suffix is the tld. We want that plus the next level up.
    return res.domain + '.' + res.suffix
