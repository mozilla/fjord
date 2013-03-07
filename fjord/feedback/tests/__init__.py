from fjord.base import browsers
from fjord.base.tests import with_save
from fjord.feedback.models import Response


USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0'


@with_save
def response(**kwargs):
    """Model maker for feedback.models.Response."""
    ua = kwargs.pop('ua', USER_AGENT)
    parsed = browsers.parse_ua(ua)
    defaults = {
        'prodchan': 'firefox.desktop.stable',

        'happy': True,
        'url': u'',
        'description': u'So awesome!',

        'user_agent': ua,
        'browser': parsed.browser,
        'browser_version': parsed.browser_version,
        'platform': parsed.platform,
        'locale': u'en-US',
    }

    defaults.update(kwargs)
    return Response(**defaults)
