from tower import ugettext_lazy as _lazy


# List of valid products accepted by the Input API
# Note: When you change this, please change the API docs, too!
PRODUCTS = [
    # (Value to store, Human readable)
    (u'Firefox OS', u'Firefox OS'),
    (u'Firefox for Android', u'Firefox for Android'),
    (u'Firefox', u'Firefox'),
]

# List of (value, display) tuples for countries Firefox OS has
# been released in.
# Values are ISO 3166 country codes.
# Display names are l10n-ized country names.
FIREFOX_OS_COUNTRIES = [
    (u'CO', _lazy('Colombia')),
    (u'VE', _lazy('Venezuela')),
    (u'PL', _lazy('Poland')),
    (u'ES', _lazy('Spain')),
]

# List of (value, display name) for Firefox OS devices that
# have been released.
# The value is a :: separated string for (manufacturer, device).
FIREFOX_OS_DEVICES = [
    (u'ZTE::Open', u'ZTE Open'),
    (u'Alcatel::OneTouch Fire', u'Alcatel OneTouch Fire'),
    (u'Geeksphone::', u'Geeksphone'),
]
