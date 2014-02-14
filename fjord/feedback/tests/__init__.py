from fjord.base import browsers
from fjord.base.tests import with_save
from fjord.feedback.models import Product, Response, ResponseEmail


USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0'


@with_save
def product(**kwargs):
    defaults = {
        'enabled': True,
        'notes': u'',
        'display_name': u'Firefox',
        'slug': u'firefox',
        'on_dashboard': True,
    }
    defaults.update(kwargs)
    if 'db_name' not in defaults:
        defaults['db_name'] = defaults['display_name']
    return Product(**defaults)


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

        'product': Response.infer_product(parsed.platform),
        'channel': u'stable',
        'version': parsed.browser_version,
        'locale': u'en-US',
    }

    defaults.update(kwargs)
    return Response(**defaults)


@with_save
def responseemail(**kwargs):
    defaults = {
        'email': 'joe@example.com'
    }

    defaults.update(kwargs)
    if 'opinion' not in kwargs:
        resp = response(save=True)
        defaults['opinion'] = resp

    return ResponseEmail(**defaults)
