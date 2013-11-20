from base64 import b64encode
from functools import wraps
import re

from pyelasticsearch.exceptions import ElasticHttpError
from ratelimit.helpers import is_ratelimited
from statsd import statsd

from fjord.feedback import config
from fjord.search.index import es_analyze


def actual_ip(req):
    """Returns the actual ip address

    Our dev, stage and prod servers are behind a reverse proxy, so the ip
    address in REMOTE_ADDR is the reverse proxy server and not the client
    ip address. The actual client ip address is in HTTP_X_CLUSTER_CLIENT_IP.

    In our local development and test environments, the client ip address
    is in REMOTE_ADDR.

    """
    return req.META.get('HTTP_X_CLUSTER_CLIENT_IP', req.META['REMOTE_ADDR'])


def actual_ip_plus_desc(req):
    """Returns actual ip address plus first 30 characters of desc

    This key is formulated to reduce double-submits.

    """
    # This pulls out the description, makes sure it's a unicode and
    # takes the first 50 characters.
    desc = unicode(req.POST.get('description', u'no description'))[:50]

    # Converts that to a utf-8 string because b64encode only works on
    # bytes--not unicode characters.
    desc = desc.encode('utf-8')

    # b64encodes that.
    desc = b64encode(desc)
    return actual_ip(req) + ':' + desc


def ratelimit(rulename, keyfun=None, rate='5/m'):
    """Rate-limiting decorator that keeps metrics via statsd

    This is just like the django-ratelimit ratelimit decorator, but is
    stacking-friendly, performs some statsd fancypants and also has
    Fjord-friendly defaults.

    :arg rulename: rulename for statsd logging---must be a string
        with letters only! look for this in statsd under
        "throttled." + rulename.
    :arg keyfun: (optional) function to generate a key for this
        throttling. defaults to actual_ip.
    :arg rate: (optional) rate to throttle at. defaults to 5/m.

    """
    if keyfun is None:
        keyfun = actual_ip

    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kwargs):
            already_limited = getattr(request, 'limited', False)
            ratelimited = is_ratelimited(
                request=request, increment=True, ip=False, method=['POST'],
                field=None, rate=rate, keys=keyfun)

            if not already_limited and ratelimited:
                statsd.incr('throttled.' + rulename)

            return fn(request, *args, **kwargs)
        return _wrapped
    return decorator


def compute_grams(text):
    """Computes bigrams from analyzed text

    :arg text: text to analyze and generate bigrams from

    :returns: list of bigrams

    >>> compute_grams(u'The quick brown fox jumped')
    [u'quick brown', u'brown fox', u'fox jumped']

    """
    if not text:
        return []

    try:
        tokens = [item['token'] for item in es_analyze(text)]
    except ElasticHttpError:
        return []

    # Remove configured stopwords.
    tokens = [token for token in tokens
              if token not in config.ANALYSIS_STOPWORDS]

    # ES analyzes the text and returns tokens that look like u'u4231'
    # for unicode characters. This nixes all of those.
    unicode_re = re.compile(r'u\d')
    tokens = [token for token in tokens if not unicode_re.match(token)]

    # Generate set of bigrams. A bigram is a set of two consecutive
    # tokens. We put them in a set because we don't want duplicates.
    # We sort them so that "youtube crash" will match "crash youtube".
    bigrams = set()
    if len(tokens) >= 2:
        for i in range(len(tokens) - 1):
            bigrams.add(u' '.join(
                sorted([tokens[i], tokens[i+1]])))

    return list(bigrams)
