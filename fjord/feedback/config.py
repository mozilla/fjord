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
    (u'BR', 'Brazil', _lazy('Brazil')),
    (u'DE', 'Germany', _lazy('Germany')),
    (u'GR', 'Greece', _lazy('Greece')),
    (u'HU', 'Hungary', _lazy('Hungary')),
    (u'CS', 'Serbia', _lazy('Serbia')),
    (u'CS', 'Montenegro', _lazy('Montenegro')),
    (u'MX', 'Mexico', _lazy('Mexico')),
    (u'PE', 'Peru', _lazy('Peru')),
]

# List of Firefox OS devices that have been released.
FIREFOX_OS_DEVICES = [
    u'ZTE Open',
    u'Alcatel OneTouch Fire',
    u'Geeksphone',
    u'LG Fireweb',
]
