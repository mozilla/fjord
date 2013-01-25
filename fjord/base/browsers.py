import re
from collections import namedtuple


# From http://msdn.microsoft.com/en-us/library/ms537503(v=vs.85).aspx
WINDOWS_VERSION = {
    'Windows NT 6.2': ('Windows', '8'),
    'Windows NT 6.1': ('Windows', '7'),
    'Windows NT 6.0': ('Windows', 'Vista'),
    'Windows NT 5.2': ('Windows', 'XP'),
    'Windows NT 5.1': ('Windows', 'XP'),
    'Windows NT 5.01': ('Windows', '2000'),
    'Windows NT 5.0': ('Windows', '2000'),
    'Windows NT 4.0': ('Windows', 'NT'),
    'Windows 98; Win 9x 4.90': ('Windows', 'ME'),
    'Windows 98': ('Windows', '98'),
    'Windows 95': ('Windows', '95'),
}


Browser = namedtuple('Browser', ['browser', 'browser_version',
    'platform', 'platform_version', 'mobile'])


def parse_ua(ua):
    """Parse user agents from Firefox and friends.

    :arg ua: a User-Agent string

    :returns: Browser with attributes:

        - browser: eg: "Firefox", or "Iceweasel".
        - browser_version: Always at least 3 dotted section, eg
          "14.0.1" or "4.0.0".
        - platform: eg: "Windows", "OS X", "Linux", or "Android"
        - platform_version: On Windows returns something like "Vista",
          or "7".  On OS X returns something like "10.6.2" or "10.4.0"
        - mobile: True if the user agent represents a mobile browser.

        If detection fails, those attributes will have None values.
    """
    mobile = 'mobile' in ua.lower()

    # If we are sure something is mobile, say True. Otherwise say None.
    no_browser = Browser(None, None, None, None, mobile or None)

    if 'firefox' not in ua.lower():
        return no_browser

    # For reference, a normal Firefox on android user agent looks like
    # Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0.2

    # Extract the part within the parenthesis, and the part after the
    # parenthesis. Inside has information about the platform, and outside has
    # information about the browser.
    match = re.match(r'^Mozilla[^(]+\(([^)]+)\) (.+)', ua)

    if match is None:
        return no_browser

    # The part in parenthesis is semi-colon seperated
    # Result: ['Android', 'Mobile', 'rv:14.0']
    platform_parts = [p.strip() for p in match.group(1).split(';')]
    # The rest is space seperated A/B pairs. Pull out both sides of the slash.
    # Result: [['Gecko', '14.0'], ['Firefox', '14.0.2']]
    browser_parts = [p.split('/') for p in match.group(2).split(' ')]

    browser = 'Firefox'
    browser_version = '0.0.0'

    for part in browser_parts:
        if 'Firefox' in part:
            browser_version = part[1]
        if 'Iceweasel' in part:
            browser = 'Iceweasel'

    platform = platform_parts.pop(0)
    platform_version = None

    while platform in ['X11', 'Ubuntu', 'U']:
        platform = platform_parts.pop(0)

    if platform in WINDOWS_VERSION.keys():
        platform, platform_version = WINDOWS_VERSION[platform]
    elif platform.startswith('Linux'):
        platform = 'Linux'
    elif platform.startswith('FreeBSD'):
        platform = 'FreeBSD'
    elif platform == 'OS X':
        for part in platform_parts:
            if 'OS X' in part:
                platform_version = part.split(' ')[-1]
                break
        platform_version = platform_version.replace('_', '.')

    # Firefox OS doesn't list a platform because "The web is the platform."
    # It is the only platform to do this, so we can still uniquely identify it.
    if platform == 'Mobile':
        platform = 'FirefoxOS'

    # Make sure browser_version is at least x.y.z
    while browser_version.count('.') < 2:
        browser_version += '.0'

    return Browser(browser, browser_version, platform, platform_version,
                   mobile)
