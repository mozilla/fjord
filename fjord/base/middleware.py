"""
The middlewares in this file do mobile detection, provide a user override,
and provide a cookie override. They must be used in the correct order.
MobileMiddleware must always come after any of the other middlewares in this
file in `settings.MIDDLEWARE_CLASSES`.
"""
import urllib
from warnings import warn

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils import translation
from django.utils.encoding import smart_str

from fjord.base import urlresolvers
from fjord.base.browsers import parse_ua
from fjord.base.templatetags.jinja_helpers import urlparams
# FIXME: from fjord.base.l10n import install_gettext


MOBILE_COOKIE = getattr(settings, 'MOBILE_COOKIE', 'mobile')


class UserAgentMiddleware(object):
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


class MobileQueryStringMiddleware(object):
    """
    Add querystring override for mobile.

    This allows the user to override mobile detection by setting
    'mobile=1' in the querystring. This will persist in a cookie
    that other the other middlewares in this file will respect.
    """
    def process_request(self, request):
        # The 'mobile' querystring overrides any prior MOBILE
        # figuring and we put it in two places.
        mobile_qs = request.GET.get('mobile', None)
        if mobile_qs == '1':
            request.MOBILE = True
            request.MOBILE_SET_COOKIE = 'yes'
        elif mobile_qs == '0':
            request.MOBILE = False
            request.MOBILE_SET_COOKIE = 'no'


class MobileMiddleware(object):
    """
    Set request.MOBILE based on cookies and UA detection.

    The set of rules to decide `request.MOBILE` is given below. If any rule
    matches, the process stops.

    1. If there is a variable `mobile` in the query string, `request.MOBILE`
       is set accordingly.
    2. If a cookie is set indicating a mobile preference, follow it.
    3. If user agent parsing has already happened, trust it's judgement about
       mobile-ness. (i.e. `request.BROWSER.mobile`)
    4. Otherwise, set `request.MOBILE` to True if the string "mobile" is in the
       user agent (case insensitive), and False otherwise.

    If there is a variable `request.MOBILE_SET_COOKIE`, it's value will be
    stored in the mobile cookie.
    """

    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '')
        mc = request.COOKIES.get(MOBILE_COOKIE)

        if hasattr(request, 'MOBILE'):
            # Our work here is done
            return

        if mc:
            request.MOBILE = (mc == 'yes')
            return

        if hasattr(request, 'BROWSER'):
            # UA Detection already figured this out.
            request.MOBILE = request.BROWSER.mobile
            return

        # Make a guess based on UA if nothing else has figured it out.
        request.MOBILE = ('mobile' in ua)

    def process_response(self, request, response):
        if hasattr(request, 'MOBILE_SET_COOKIE'):
            cookie_value = request.MOBILE_SET_COOKIE
            response.set_cookie(MOBILE_COOKIE, cookie_value)
        return response


class LocaleURLMiddleware(object):
    """
    1. Search for the locale.
    2. Save it in the request.
    3. Strip them from the URL.
    """

    def __init__(self):
        if not settings.USE_I18N or not settings.USE_L10N:
            warn('USE_I18N or USE_L10N is False but LocaleURLMiddleware is '
                 'loaded. Consider removing fjord.base.middleware.'
                 'LocaleURLMiddleware from your MIDDLEWARE_CLASSES setting.')

        self.exempt_urls = getattr(settings, 'FF_EXEMPT_LANG_PARAM_URLS', ())

    def _is_lang_change(self, request):
        """Return True if the lang param is present and URL isn't exempt."""
        if 'lang' not in request.GET:
            return False

        return not any(request.path.endswith(url) for url in self.exempt_urls)

    def process_request(self, request):
        prefixer = urlresolvers.Prefixer(request)
        urlresolvers.set_url_prefix(prefixer)
        full_path = prefixer.fix(prefixer.shortened_path)

        if self._is_lang_change(request):
            # Blank out the locale so that we can set a new one. Remove lang
            # from the query params so we don't have an infinite loop.
            prefixer.locale = ''
            new_path = prefixer.fix(prefixer.shortened_path)
            query = dict((smart_str(k), request.GET[k]) for k in request.GET)
            query.pop('lang')
            return HttpResponsePermanentRedirect(urlparams(new_path, **query))

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.quote(full_path.encode('utf-8'))

            if query_string:
                full_path = '%s?%s' % (full_path, query_string)

            response = HttpResponsePermanentRedirect(full_path)

            # Vary on Accept-Language if we changed the locale
            old_locale = prefixer.locale
            new_locale, _ = urlresolvers.split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            return response

        request.path_info = '/' + prefixer.shortened_path
        request.locale = prefixer.locale
        translation.activate(prefixer.locale)
        # FIXME
        # install_gettext()
