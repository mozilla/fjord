from base64 import b64encode
from functools import wraps

from ratelimit.helpers import is_ratelimited
from statsd import statsd


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


def ratelimit(rulename, key=None, rate='5/m'):
    """Rate-limiting decorator that keeps metrics via statsd

    This is just like the django-ratelimit ratelimit decorator, but is
    stacking-friendly, performs some statsd fancypants and also has
    Fjord-friendly defaults.

    :arg rulename: rulename for statsd logging---must be a string
        with letters only! look for this in statsd under
        "throttled." + rulename.
    :arg keys: (optional) function to generate a key for this
        throttling. defaults to actual_ip.
    :arg rate: (optional) rate to throttle at. defaults to 5/m.

    """
    if key is None:
        key = actual_ip

    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kwargs):
            already_limited = getattr(request, 'limited', False)
            ratelimited = is_ratelimited(
                request=request, increment=True, ip=False, method=['POST'],
                field=None, rate=rate, keys=key)

            if not already_limited and ratelimited:
                statsd.incr('throttled.' + rulename)

            return fn(request, *args, **kwargs)
        return _wrapped
    return decorator
