import re

from mobility.middleware import USER_AGENTS as mobile_ua_re


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


def parse_ua(ua):
    """Parse user agents from Firefox and friends.

    Returns a dictionary containing the key:
    - browser: eg: "Firefox", or "Iceweasel".
    - browser_version: Always at least 3 dotted section, eg "14.0.1" or "4.0.0".
    - platform: eg: "Windows", "OS X", "Linux", or "Android"
    - platform_version: On Windows returns something like "Vista", or "7".
        On OS X returns something like "10.6.2" or "10.4.0"
    - mobile: True if the user agent rperesents a mobile browser.

    If detection fails, the above values will be `None`.
    """
    no_browser = {
        'browser': None,
        'browser_version': None,
        'platform': None,
        'platform_version': None,
        'mobile': None
    }

    if 'firefox' not in ua.lower():
        return no_browser

    match = re.match(r'^Mozilla[^(]+\(([^)]+)\) (.+)', ua)

    if match is None:
        return no_browser

    platform_parts = [p.strip() for p in match.group(1).split(';')]
    browser_parts = [p.split('/') for p in match.group(2).split(' ')]

    browser = 'Firefox'
    browser_version = '0.0.0'

    for part in browser_parts:
        if 'Firefox' in part:
            browser_version = part[-1]
        if 'Iceweasel' in part:
            browser = 'Iceweasel'

    platform = platform_parts.pop(0)
    platform_version = None

    while platform in ['X11', 'Ubuntu', 'U']:
        platform = platform_parts.pop(0)

    if platform in WINDOWS_VERSION.keys():
        platform, platform_version = WINDOWS_VERSION[platform]

    if platform.startswith('Linux'):
        platform = 'Linux'
    elif platform.startswith('FreeBSD'):
        platform = 'FreeBSD'
    elif platform == 'OS X':
        for part in platform_parts:
            if 'OS X' in part:
                platform_version = part.split(' ')[-1]
                break
        platform_version = platform_version.replace('_', '.')

    while browser_version.count('.') < 2:
        browser_version += '.0'

    mobile = 'mobile' in ua.lower() or bool(mobile_ua_re.match(ua))

    return {
        'browser': browser,
        'browser_version': browser_version,
        'platform': platform,
        'platform_version': platform_version,
        'mobile': mobile
    }
