from datetime import datetime
from functools import wraps
import time

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.utils.feedgenerator import Atom1Feed

from funfactory.urlresolvers import reverse
from product_details import product_details
from rest_framework.throttling import AnonRateThrottle
from statsd import statsd


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


def smart_int(s, fallback=0):
    """Convert a string to int, with fallback for invalid strings or types."""
    try:
        return int(float(s))
    except (ValueError, TypeError, OverflowError):
        return fallback


def smart_datetime(s, fmt='%Y-%m-%d', fallback=None):
    """Convert a string to a datetime, with a fallback for invalid input.

    Note that this won't take ``datetime``s as input, only strings. It is
    different than ``smart_int`` in this way.

    :arg s: The string to convert to a date.
    :arg fmt: Format to use to parse the string into a date.
        Default: ``'%Y-%m-%d'``.
    :arg fallback: Value to use in case of an error. Default: ``None``.

    """
    try:
        dt = datetime.strptime(s, fmt)
        # The strftime functions require a year >= 1900, so if this
        # has a year before that, then it's not a valid date.
        if dt.year >= 1900:
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
        if item['link_related']:
            handler.addQuickElement(
                'link',
                attrs={'href': item['link_related'], 'rel': 'related'})


class MeasuredAnonRateThrottle(AnonRateThrottle):
    """On throttle failure, does a statsd call"""
    def throttle_failure(self):
        statsd.incr('api.throttle.failure')


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


analyzer_required = permission_required(
    'analytics.can_view_dashboard',
    raise_exception=True)
