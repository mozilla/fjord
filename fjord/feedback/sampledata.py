from fjord.base import browsers
from fjord.feedback.tests import response


FIREFOX_LINUX_17 = (
    'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0')


def create_response(happy, description, url=u'', ua=FIREFOX_LINUX_17,
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
    obj = response(**data)
    obj.save()
    return obj


def generate_sampledata(options):
    # Create 5 happy opinions.
    create_response(True, u'Firefox is great!')
    create_response(True, u'Made me pancakes!')
    create_response(True, u'I love it!')
    create_response(True, u'Firefox now default browser!')
    create_response(True, u'My bestest friend!')

    # Create 5 sad opinions.
    create_response(False, u'Too much orange!', u'http://example.com/')
    create_response(False, u'Ate my baby-sister!', u'http://google.com/')
    create_response(False, u'Too fast!', u'http://pyvideo.org/')
    create_response(False, u'Too easy to use!', u'http://github.com/')
    create_response(False, u'Parked my car in wrong spot!',
                  u'http://facebook.com/')
