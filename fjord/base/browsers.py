import re
from collections import namedtuple


# From http://msdn.microsoft.com/en-us/library/ms537503(v=vs.85).aspx
WINDOWS_VERSION = {
    'Windows NT 10.0': ('Windows', '10'),
    'Windows NT 6.4': ('Windows', '10'),
    'Windows NT 6.3': ('Windows', '8.1'),
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

GECKO_TO_FIREFOXOS_VERSION = {
    '18.0': '1.0',
    '18.1': '1.1',
    '26.0': '1.2',
    '28.0': '1.3'
}

UNKNOWN = ''

Browser = namedtuple('Browser', [
    'browser', 'browser_version', 'platform', 'platform_version',
    'mobile'])


def parse_ua(ua):
    """Parse user agents from Firefox and friends.

    :arg ua: a User-Agent string

    :returns: Browser namedtuple with attributes:

        - browser: "Unknown" or a browser like "Firefox", "Iceweasel", etc.
        - browser_version: "Unknown" or a 3 dotted section like "14.0.1",
          "4.0.0", etc.
        - platform: "Unknown" or a platform like "Windows", "OS X",
          "Linux", "Android", etc.
        - platform_version: "Unknown or something like "Vista" or "7" for
          Windows or something like "10.6.2" or "10.4.0" for OSX.
        - mobile: True if the user agent represents a mobile browser.
          False if it's definitely not a mobile browser. None if we
          don't know.

    .. Note::

       This should never throw an exception. If it does, that's
       a bug.

    """
    mobile = 'mobile' in ua.lower()

    # Unknown values are UNKNOWN. If we are sure something is mobile,
    # say True. Otherwise say None.
    no_browser = Browser(UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
                         mobile or None)

    if 'firefox' not in ua.lower():
        return no_browser

    # For reference, a normal Firefox on android user agent looks like
    # Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0.2

    # Extract the part within the parenthesis, and the part after the
    # parenthesis. Inside has information about the platform, and
    # outside has information about the browser.
    match = re.match(r'^Mozilla[^(]+\(([^)]+)\) (.+)', ua)

    if match is None:
        # If match is None here, then this is not a UA we can infer
        # browser information from, so we return unknown.
        return no_browser

    # The part in parenthesis is semi-colon seperated
    # Result: ['Android', 'Mobile', 'rv:14.0']
    platform_parts = [p.strip() for p in match.group(1).split(';')]
    # The rest is space seperated A/B pairs. Pull out both sides of
    # the slash.
    # Result: [['Gecko', '14.0'], ['Firefox', '14.0.2']]
    browser_parts = [p.split('/') for p in match.group(2).split(' ')]

    browser = 'Firefox'
    browser_version = UNKNOWN

    for part in browser_parts:
        if 'Firefox' in part and len(part) > 1:
            browser_version = part[1]
        elif 'Iceweasel' in part:
            browser = 'Iceweasel'

    platform = platform_parts.pop(0)
    platform_version = UNKNOWN

    while platform in ['X11', 'Ubuntu', 'U']:
        platform = platform_parts.pop(0)

    if platform == 'Windows':
        # Firefox 3.6 has the Windows version later in the parts. So
        # skim the parts to find a version that's in WINDOWS_VERSION.
        # If we don't find anything, just leave things as is.
        possible_platforms = [p for p in platform_parts
                              if p in WINDOWS_VERSION]
        if possible_platforms:
            platform = possible_platforms[0]

    if platform in WINDOWS_VERSION.keys():
        platform, platform_version = WINDOWS_VERSION[platform]
    elif platform.startswith('Linux'):
        platform = 'Linux'
    elif platform.startswith('FreeBSD'):
        platform = 'FreeBSD'
    elif platform in ('OS X', 'Macintosh'):
        for part in platform_parts:
            if 'OS X' in part:
                # If OS X is in one of the parts, then we normalize
                # the platform to 'OS X'.
                platform = 'OS X'
                platform_version = part.split(' ')[-1]
                break
        if platform_version:
            platform_version = platform_version.replace('_', '.')

    # Firefox OS doesn't list a platform because "The web is the
    # platform."  It is the only platform to do this, so we can still
    # uniquely identify it.
    if platform == 'Mobile':
        platform = 'Firefox OS'
        browser = 'Firefox OS'

        # Set versions to UNKNOWN. This handles the case where the
        # version of Gecko doesn't line up with a Firefox OS product
        # release.
        browser_version = UNKNOWN
        platform_version = UNKNOWN

        # Now try to infer the Firefox OS version from the Gecko
        # version. If we can, then we set the browser_version and
        # platform_version.
        for part in browser_parts:
            if 'Gecko' in part and len(part) > 1:
                fxos_version = GECKO_TO_FIREFOXOS_VERSION.get(part[1])
                if fxos_version is not None:
                    browser_version = fxos_version
                    platform_version = fxos_version
                    break

    # Make sure browser_version is at least x.y for non-Firefox OS
    # browsers.
    if (browser != 'Firefox OS'
            and browser_version != UNKNOWN
            and browser_version.count('.') < 1):
        browser_version += '.0'

    return Browser(browser, browser_version, platform, platform_version,
                   mobile)
