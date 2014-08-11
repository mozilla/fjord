import datetime
import json
import re
import time
from functools import wraps
from hashlib import md5

from django.contrib.auth.decorators import permission_required
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect
)
from django.utils.dateparse import parse_date
from django.utils.encoding import force_str
from django.utils.feedgenerator import Atom1Feed

from product_details import product_details
from ratelimit.helpers import is_ratelimited
from rest_framework.throttling import SimpleRateThrottle
from statsd import statsd

from fjord.base.urlresolvers import reverse


class JSONDatetimeEncoder(json.JSONEncoder):
    def default(self, value):
        if hasattr(value, 'strftime'):
            return value.isoformat()
        return super(JSONDatetimeEncoder, self).default(value)


def translate_country_name(current_language, country_code, country_name,
                           country_name_l10n):
    """Translates country name from product details or gettext

    It might seem a bit weird we're not doing the _lazy gettext
    translation here, but if we did, then we'd be translating a
    variable value rather than a string and then it wouldn't get
    picked up by extract script.

    :arg current_language: the language of the user viewing the page
    :arg country_code: the iso 3166 two-letter country code
    :arg country_name: the country name
    :arg country_name_l10n: the country name wrapped in a lazy gettext call

    :returns: translated country name

    """
    # FIXME: this is a lousy way to alleviate the problem where we
    # have a "locale" and we really need a "language".
    language_fix = {
        'es': 'es-ES',
    }

    current_language = language_fix.get(current_language, current_language)

    # If the country name has been translated, then use that
    if unicode(country_name) != unicode(country_name_l10n):
        return country_name_l10n

    current_language = current_language.split('-')
    current_language[0] = current_language[0].lower()
    if len(current_language) > 1:
        current_language[1] = current_language[1].upper()
    current_language = '-'.join(current_language)

    country_code = country_code.lower()

    try:
        countries = product_details.get_regions(current_language)
    except IOError:
        return country_name

    return countries.get(country_code, country_name)


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


def smart_str(s, fallback=u''):
    """Returns the string or the fallback if it's not a string"""
    if isinstance(s, basestring):
        return s

    return fallback


def smart_int(s, fallback=0):
    """Convert a string to int, with fallback for invalid strings or types."""
    try:
        return int(float(s))
    except (ValueError, TypeError, OverflowError):
        return fallback


def smart_timedelta(s, fallback=None):
    """Convert s to a datetime.timedelta with a fallback for invalid input.

    :arg s: The string to convert to a timedelta.
    :arg fallback: Value to use in case of an error. Default: ``None``.

    """
    if isinstance(s, datetime.timedelta):
        return s

    # FIXME: Doing this manually for now for specific deltas. We can
    # figure out how we want this to operate in the future.
    if s == '1d':
        return datetime.timedelta(days=1)
    if s == '7d':
        return datetime.timedelta(days=7)
    if s == '14d':
        return datetime.timedelta(days=14)
    return fallback


def smart_date(s, fallback=None):
    """Convert a string to a datetime.date with a fallback for invalid input.

    :arg s: The string to convert to a date.
    :arg fallback: Value to use in case of an error. Default: ``None``.

    """
    if isinstance(s, datetime.date):
        return s

    try:
        dt = parse_date(s)

        # The strftime functions require a year >= 1900, so if this
        # has a year before that, then we treat it as an invalid date so
        # later processing doesn't get hosed.
        if dt and dt.year >= 1900:
            return dt
    except (ValueError, TypeError):
        pass

    return fallback


def smart_bool(s, fallback=False):
    """Convert a string that has a semantic boolean value to a real boolean.

    Note that this is not the same as ``s`` being "truthy". The string
    ``'False'`` will be returned as False, even though it is Truthy, and non-
    boolean values like ``'apple'`` would return the fallback parameter, since
    it doesn't represent a boolean value.

    """
    try:
        s = s.lower()
        if s in ['true', 't', 'yes', 'y', '1']:
            return True
        elif s in ['false', 'f', 'no', 'n', '0']:
            return False
    except AttributeError:
        pass

    return fallback


def epoch_milliseconds(d):
    """Convert a datetime to a number of milliseconds since the epoch."""
    return time.mktime(d.timetuple()) * 1000


class FakeLogger(object):
    """Fake logger that we can pretend is a Python Logger

    Why? Well, because Django has logging settings that prevent me
    from setting up a logger here that uses the stdout that the Django
    BaseCommand has. At some point p while fiddling with it, I
    figured, 'screw it--I'll just write my own' and did.

    The minor ramification is that this isn't a complete
    implementation so if it's missing stuff, we'll have to add it.
    """

    def __init__(self, stdout):
        self.stdout = stdout

    def _out(self, level, msg, *args):
        msg = msg % args
        self.stdout.write('%s %-8s: %s\n' % (
                time.strftime('%H:%M:%S'), level, msg))

    def info(self, msg, *args):
        self._out('INFO', msg, *args)

    def error(self, msg, *args):
        self._out('ERROR', msg, *args)


class Atom1FeedWithRelatedLinks(Atom1Feed):
    """Atom1Feed with related links

    This adds a "link_related" item as::

        <link rel="related">url</link>

    """

    def add_item_elements(self, handler, item):
        super(Atom1FeedWithRelatedLinks, self).add_item_elements(handler, item)
        if item.get('link_related'):
            handler.addQuickElement(
                'link',
                attrs={'href': item['link_related'], 'rel': 'related'})


def actual_ip(req):
    """Returns the actual ip address

    Our dev, stage and prod servers are behind a reverse proxy, so the ip
    address in REMOTE_ADDR is the reverse proxy server and not the client
    ip address. The actual client ip address is in HTTP_X_CLUSTER_CLIENT_IP.

    In our local development and test environments, the client ip address
    is in REMOTE_ADDR.

    """
    return req.META.get('HTTP_X_CLUSTER_CLIENT_IP', req.META['REMOTE_ADDR'])


def actual_ip_plus_context(contextfun):
    """Returns a key function that adds md5 hashed context to the key"""
    def _actual_ip_plus_context(req, *args, **kwargs):
        # Force whatever comes out of contextfun to be bytes.
        context = force_str(contextfun(req))

        # md5 hash that.
        hasher = md5()
        hasher.update(context)
        context = hasher.hexdigest()

        # Then return the ip address plus a : plus the desc md5 hash.
        return actual_ip(req) + ':' + context
    return _actual_ip_plus_context


def ratelimit(rulename, keyfun=actual_ip, rate='5/m'):
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


RATE_RE = re.compile(r'^(\d+)/(\d*)([smhd])$')

class RatelimitThrottle(SimpleRateThrottle):
    """This wraps the django-ratelimit ratelimiter in a DRF class

    Django Rest Framework has its own throttling system. That's great,
    but we're already using django-ratelimit. So this wraps
    django-ratelimit throttling in the Django Rest Framework structure
    so I can have a unified throttling backend for regular and API
    views.

    .. Note::

       Return an instance of this in the `get_throttles` method. Don't
       use this with `throttled_classes` property because it requires
       other parameters to instantiate.

       e.g.::

           class MyThrottle(AnonRateThrottle):
               def get_throttles(self):
                   return [
                       RatelimitThrottle(
                           rulename='double_submit',
                           rate='1/10m'
                       )
                   ]

    """
    def __init__(self, rulename, keyfun=None, rate='5/m', methods=('POST',)):
        self.rulename = rulename
        self.rate = rate
        self.num_requests, self.duration = self.parse_rate(rate)
        self.keyfun = keyfun or actual_ip
        self.methods = methods

    def get_cache_key(self, request, view):
        return self.keyfun(request)

    def parse_rate(self, rate):
        """Handles num/(multi * period) like 1/10m"""
        num, multiplier, period = RATE_RE.match(rate).groups()

        num = int(num)
        multiplier = int(multiplier or 1)
        period = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period]
        return (num, (multiplier * period))

    def allow_request(self, request, view):
        ratelimited = is_ratelimited(
            request=request, increment=True, ip=False, method=self.methods,
            field=None, rate=self.rate, keys=self.keyfun)

        if ratelimited:
            # Failed rate-limiting, so this request is not allowed.
            statsd.incr('throttled.' + self.rulename)
            return self.throttle_failure()

        # Did not trigger rate-limiting, so this request is allowed.
        return self.throttle_success()

    def throttle_success(self):
        return True

    def throttle_failure(self):
        """Called when a request has failed due to throttling"""
        return False

    def wait(self):
        # We don't want to calculate the actual wait time, so we cheat
        # here and just return the duration.
        return self.duration


def check_new_user(fun):
    @wraps(fun)
    def _wrapped_view(request, *args, **kwargs):
        # Do this here to avoid circular imports
        from fjord.base.models import Profile

        try:
            request.user.profile
        except AttributeError:
            pass
        except Profile.DoesNotExist:
            url = reverse('new-user-view') + '?next=' + request.path
            return HttpResponseRedirect(url)

        return fun(request, *args, **kwargs)

    return _wrapped_view


def cors_enabled(origin, methods=['GET']):
    """A simple decorator to enable CORS."""
    def decorator(f):
        @wraps(f)
        def decorated_func(request, *args, **kwargs):
            if request.method == 'OPTIONS':
                # preflight
                if ('HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META and
                        'HTTP_ACCESS_CONTROL_REQUEST_HEADERS' in request.META):

                    response = HttpResponse()
                    response['Access-Control-Allow-Methods'] = ", ".join(
                        methods)

                    # TODO: We might need to change this
                    response['Access-Control-Allow-Headers'] = \
                        request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']
                else:
                    return HttpResponseBadRequest()
            elif request.method in methods:
                response = f(request, *args, **kwargs)
            else:
                return HttpResponseBadRequest()

            response['Access-Control-Allow-Origin'] = origin
            return response
        return decorated_func
    return decorator


analyzer_required = permission_required(
    'analytics.can_view_dashboard',
    raise_exception=True)


def class_to_path(cls):
    """Given a class, returns the class path"""
    return ':'.join([cls.__module__, cls.__name__])


def path_to_class(path):
    """Given a class path, returns the class"""
    module_path, cls_name = path.split(':')
    module = __import__(module_path, fromlist=[cls_name])
    cls = getattr(module, cls_name)
    return cls


def instance_to_key(instance):
    """Given an instance, returns a key

    :arg instance: The model instance to generate a key for

    :returns: A string representing that specific instance

    .. Note::

       If you ever make a code change that moves the model to some
       other Python module, then the keys for those model instances
       will fail.

    """
    cls = instance.__class__
    return ':'.join([cls.__module__, cls.__name__, str(instance.pk)])


def key_to_instance(key):
    """Given a key, returns the instance

    :raises DoesNotExist: if the instance doesn't exist
    :raises ImportError: if there's an import error
    :raises AttributeError: if the class doesn't exist in the module

    """
    module_path, cls_name, id_ = key.split(':')
    module = __import__(module_path, fromlist=[cls_name])
    cls = getattr(module, cls_name)
    instance = cls.objects.get(pk=int(id_))

    return instance
