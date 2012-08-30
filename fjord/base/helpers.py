from django.contrib.humanize.templatetags import humanize

from jingo import register


@register.filter
def naturaltime(*args):
    return humanize.naturaltime(*args)
