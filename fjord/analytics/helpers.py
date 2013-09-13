from jingo import register
from tower import ugettext_lazy as _lazy


@register.filter
def unknown(text):
    """Converts empty string to localized "Unknown"
    """
    return _lazy('Unknown') if text == '' else text
