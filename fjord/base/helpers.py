import time
import json
from datetime import datetime, timedelta

from django.contrib.humanize.templatetags import humanize

from jingo import register
from tower import ugettext_lazy as _lazy
from product_details import product_details


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
def locale_name(locale, native=False, default=_lazy('Unknown')):
    """Convert a locale code into a human readable locale name."""
    if locale in product_details.languages:
        display_locale = 'native' if native else 'English'
        return product_details.languages[locale][display_locale]
    else:
        return default


@register.function
def date_ago(days=0):
    now = datetime.now()
    diff = timedelta(days=days)
    return (now - diff).date()


@register.function
def to_datetime_string(dt):
    """Converts date/datetime to '%Y-%m-%dT%H:%M:%S'"""
    return dt.strftime('%Y-%m-%dT%H:%M:%S')


@register.function
def to_date_string(dt):
    """Converts date/datetime to '%Y-%m-%d'"""
    return dt.strftime('%Y-%m-%d')
