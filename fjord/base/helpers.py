from django.contrib.humanize.templatetags import humanize

from jingo import register
import jinja2


@register.filter
def naturaltime(*args):
    return humanize.naturaltime(*args)


@register.filter
@register.function
def yell(text):
    return text.upper()
