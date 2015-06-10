import datetime
import json
import time
import urllib
import urlparse

from django.contrib.humanize.templatetags import humanize
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template import defaultfilters
from django.utils.encoding import smart_str
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _lazy

import jinja2
from jingo import register
from product_details import product_details

from fjord.base.urlresolvers import reverse


# Yanking filters from Django.
register.filter(strip_tags)
register.filter(defaultfilters.timesince)
register.filter(defaultfilters.truncatewords)


@register.function
def thisyear():
    """The current year."""
    return jinja2.Markup(datetime.date.today().year)


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    return reverse(viewname, args=args, kwargs=kwargs)


@register.filter
def urlparams(url_, hash=None, **query):
    """Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    # Use dict(parse_qsl) so we don't get lists of values.
    q = url.query
    query_dict = dict(urlparse.parse_qsl(smart_str(q))) if q else {}
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


@register.filter
def urlencode(txt):
    """Url encode a path."""
    if isinstance(txt, unicode):
        txt = txt.encode('utf-8')
    return urllib.quote_plus(txt)


@register.function
def static(path):
    return staticfiles_storage.url(path)


@register.filter
def naturaltime(*args):
    return humanize.naturaltime(*args)


def json_handle_datetime(obj):
    """Convert a datetime obj to a number of milliseconds since epoch.

    This uses milliseconds since this is probably going to be used to
    feed JS, and JS timestamps use milliseconds.

    """
    try:
        return time.mktime(obj.timetuple()) * 1000
    except AttributeError:
        return obj


@register.filter
def to_json(data):
    return json.dumps(data, default=json_handle_datetime)


@register.filter
def locale_name(locale, native=False, default=_lazy(u'Unknown')):
    """Convert a locale code into a human readable locale name"""
    if locale in product_details.languages:
        display_locale = 'native' if native else 'English'
        return product_details.languages[locale][display_locale]
    else:
        return default


@register.function
def date_ago(days=0):
    now = datetime.datetime.now()
    diff = datetime.timedelta(days=days)
    return (now - diff).date()


@register.function
def to_datetime_string(dt):
    """Converts date/datetime to '%Y-%m-%dT%H:%M:%S'"""
    return dt.strftime('%Y-%m-%dT%H:%M:%S')


@register.function
def to_date_string(dt):
    """Converts date/datetime to '%Y-%m-%d'"""
    return dt.strftime('%Y-%m-%d')


@register.function
def displayname(user):
    """Returns the best display name for the user"""
    return user.first_name or user.email
