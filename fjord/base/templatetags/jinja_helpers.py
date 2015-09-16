import datetime
import json
import time
import urllib
import urlparse

from django.utils.encoding import smart_str, smart_text
from django.utils.translation import ugettext_lazy as _lazy

import jinja2
from django_jinja import library
from product_details import product_details

from fjord.base.urlresolvers import reverse


@library.filter
def unknown(text):
    """Converts empty string to localized 'Unknown'"""
    return text if text else _lazy('Unknown')


@library.global_function
def url(viewname, *args, **kwargs):
    """Performs our localized reverse"""
    return reverse(viewname, args=args, kwargs=kwargs)


@library.filter
def urlparams(url_, hash=None, **query):
    """Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    # Use dict(parse_qsl) so we don't get lists of values.
    q = url.query
    query_dict = dict(urlparse.parse_qsl(smart_text(q))) if q else {}
    query_dict.update((k, v) for k, v in query.items())

    query_string = _urlencode([(k, v) for k, v in query_dict.items()
                               if v is not None])
    new = urlparse.ParseResult(url.scheme, url.netloc, url.path, url.params,
                               query_string, fragment)
    return new.geturl()


def _urlencode(items):
    """A Unicode-safe URLencoder."""
    try:
        return urllib.urlencode(items)
    except UnicodeEncodeError:
        return urllib.urlencode([(k, smart_str(v)) for k, v in items])


def json_handle_datetime(obj):
    """Convert a datetime obj to a number of milliseconds since epoch.

    This uses milliseconds since this is probably going to be used to
    feed JS, and JS timestamps use milliseconds.

    """
    try:
        return time.mktime(obj.timetuple()) * 1000
    except AttributeError:
        return obj


@library.filter
def to_json(data):
    return json.dumps(data, default=json_handle_datetime)


@library.filter
def locale_name(locale, native=False, default=_lazy(u'Unknown')):
    """Convert a locale code into a human readable locale name"""
    if locale in product_details.languages:
        display_locale = 'native' if native else 'English'
        return product_details.languages[locale][display_locale]
    else:
        return default


@library.global_function
def date_ago(days=0):
    now = datetime.datetime.now()
    diff = datetime.timedelta(days=days)
    return (now - diff).date()


@library.global_function
def to_date_string(dt):
    """Converts date/datetime to '%Y-%m-%d'"""
    return dt.strftime('%Y-%m-%d')


@library.global_function
def displayname(user):
    """Returns the best display name for the user"""
    return user.first_name or user.email


@library.filter
def fe(s, *args, **kwargs):
    """Format a safe string with potentially unsafe arguments

    :returns: safe string

    """
    args = [jinja2.escape(smart_text(v)) for v in args]

    for k in kwargs:
        kwargs[k] = jinja2.escape(smart_text(kwargs[k]))

    return jinja2.Markup(s.format(*args, **kwargs))


@library.filter
def ifeq(a, b, text):
    """Return ``text`` if ``a == b``."""
    return jinja2.Markup(text if a == b else '')
