from django.utils.translation import ugettext_lazy as _lazy

from jingo import register

from fjord.feedback.config import CODE_TO_COUNTRY


@register.filter
def country_name(country, native=False, default=_lazy(u'Unknown')):
    """Convert a country code into a human readable country name"""
    if country in CODE_TO_COUNTRY:
        display_locale = 'native' if native else 'English'
        return CODE_TO_COUNTRY[country][display_locale]
    else:
        return default
