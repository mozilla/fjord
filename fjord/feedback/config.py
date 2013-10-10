from tower import ugettext_lazy as _lazy


# List of valid products accepted by the Input API
# Note: When you change this, please change the API docs, too!
PRODUCTS = [
    # (Value to store, Human readable)
    (u'Firefox OS', u'Firefox OS'),
    (u'Firefox for Android', u'Firefox for Android'),
    (u'Firefox', u'Firefox'),
]

# List of (value, name, _lazy(name)) tuples for countries Firefox OS has
# been released in.
# Values are ISO 3166 country codes.
# Names are the country names.
# _lazy(name) causes extract to pick up the name so it can be localized.
FIREFOX_OS_COUNTRIES = [
    (u'CO', 'Colombia', _lazy('Colombia')),
    (u'VE', 'Venezuela', _lazy('Venezuela')),
    (u'PL', 'Poland', _lazy('Poland')),
    (u'ES', 'Spain', _lazy('Spain')),
]

# List of (value, display name) for Firefox OS devices that
# have been released.
# The value is a :: separated string for (manufacturer, device).
FIREFOX_OS_DEVICES = [
    (u'ZTE::Open', u'ZTE Open'),
    (u'Alcatel::OneTouch Fire', u'Alcatel OneTouch Fire'),
    (u'Geeksphone::', u'Geeksphone'),
]
