from django.utils.translation import ugettext_lazy as _lazy

from jingo import register


@register.filter
def unknown(text):
    """Converts empty string to localized "Unknown"
    """
    return _lazy('Unknown') if text == '' else text
