from mobility.middleware import COOKIE


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
