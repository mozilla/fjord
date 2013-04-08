from datetime import datetime, timedelta
import time
import json

from django.contrib.humanize.templatetags import humanize

from jingo import register

from tower import ugettext_lazy as _lazy

from product_details import product_details


@register.filter
def naturaltime(*args):
    return humanize.naturaltime(*args)


def json_handle_datetime(obj):
    """Convert a datetime obj to a number of milliseconds since the epoch.

    This uses milliseconds since this is probably going to be used to feed JS,
    and JS timestamps use milliseconds.

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
def convert_date_string(datetime_string, in_fmt='%Y-%m-%dT%H:%M:%S',
                        out_fmt='%Y-%m-%d'):
    """Converts date/datetime string from in_fmt to out_fmt

    :arg date: string represnting datetime
    :arg in_fmt: the format the datetime_string is in
    :arg out_fmt: the format to return

    :returns: date in YYYY-MM-DD or format specified by out_fmt

    :raises TypeError, ValueError: bad datetime_string input (None,
        empty string, doesn't match in_fmt, ...)

    Example:

    >>> to_date_string('2013-04-03T14:42:15')
    '2013-04-03'


    """
    # u'2013-04-03T14:42:15'
    return datetime.strptime(datetime_string, in_fmt).strftime(out_fmt)
