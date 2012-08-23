from mobility.middleware import COOKIE

from fjord.base.browsers import parse_ua


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


class ParseUseragentMiddleware(object):
    """Add ``request.BROWSER`` which has information from the User-Agent

    ``request.BROWSER`` has the following attributes:

    - browser: The user's browser, eg: "Firefox".
    - browser_version: The browser's version, eg: "14.0.1"
    - platform: The general platform the user is using, eg "Windows".
    - platform_version: The version of the platform, eg. "XP" or "10.6.2".
    - mobile: If the client is using a mobile device. `True` or `False`.

    Any of the above may be `None` if detection fails.
    """

    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '')
        request.BROWSER = parse_ua(ua)
