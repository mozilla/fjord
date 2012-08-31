from fjord.base import browsers
from fjord.feedback.tests import simple


FIREFOX_LINUX_17 = (
    'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0')


def create_simple(happy, description, url=u'', ua=FIREFOX_LINUX_17,
                  locale=u'en-US'):
    parsed = browsers.parse_ua(ua)
    data = {
        'happy': happy,
        'url': url,
        'description': description,

        'user_agent': ua,
        'browser': parsed.browser,
        'browser_version': parsed.browser_version,
        'platform': parsed.platform,
        'locale': locale,
    }
    obj = simple(**data)
    obj.save()
    return obj


def generate_sampledata():
    # Create 5 happy opinions.
    create_simple(True, u'Firefox is great!')
    create_simple(True, u'Made me pancakes!')
    create_simple(True, u'I love it!')
    create_simple(True, u'Firefox now default browser!')
    create_simple(True, u'My bestest friend!')

    # Create 5 sad opinions.
    create_simple(False, u'Too much orange!', u'http://example.com/')
    create_simple(False, u'Ate my baby-sister!', u'http://google.com/')
    create_simple(False, u'Too fast!', u'http://pyvideo.org/')
    create_simple(False, u'Too easy to use!', u'http://github.com/')
    create_simple(False, u'Parked my car in wrong spot!',
                  u'http://facebook.com/')
