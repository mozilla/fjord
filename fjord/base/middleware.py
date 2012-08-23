from mobility.middleware import COOKIE

from fjord.base.browsers import parse_ua, Browser


class MobileQueryStringOverrideMiddleware(object):
    """
    This allows the user to override mobile detection by setting the
    'mobile=1' or 'mobile=true' in the querystring. This will persist
    in the cookie that django-mobility uses until they set it
    differently or manually delete the cookie.
    """
    def process_request(self, request):
        # The 'mobile' querystring overrides any prior MOBILE
        # figuring and we put it in two places.
        mobile_qs = request.GET.get('mobile', None)
        if mobile_qs is not None:
            if mobile_qs in ('1', 'true'):
                request.MOBILE = True
                request.MOBILE_QS = 'on'
            else:
                request.MOBILE = False
                request.MOBILE_QS = 'off'

    def process_response(self, request, response):
        mobile_qs = getattr(request, 'MOBILE_QS', None)
        if mobile_qs is not None:
            response.set_cookie(COOKIE, mobile_qs)
        return response


class ParseUserAgentMiddleware(object):
    """Add `request.client`, which contains information from the user agent.

    Contains the keys:

    - BROWSER: The user's browser, eg: "Firefox".
    - BROWSER_VERSION: The browser's version, eg: "14.0.1"
    - PLATFORM: The general platform the user is using, eg "Windows".
    - PLATFORM_VERSION: The version of the platform, eg. "XP" or "10.6.2".
    - MOBILE: If the client is using a mobile device. `True` or `False`.

    Any of the above may be `None` if detection fails.
    """

    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '')
        request.BROWSER = Browser(**parse_ua(ua))
