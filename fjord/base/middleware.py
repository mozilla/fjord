class MobileDetectionMiddleware(object):
    """
    If the user has flagged that they are mobile or we were able to
    detect that the user is a mobile user, store that the user is a
    mobile user. If we find that we've previously stored that the user
    is on mobile, tell the request that the user is a mobile user.

    (N.B.: Lifted from Zamboni.)
    """
    def process_request(self, request):
        mobile_qs = request.GET.get('mobile', False)
        if mobile_qs:
            if mobile_qs == 'false':
                request.delete_cookie('mobile')
            else:
                request.set_cookie('mobile', 'true')

        request.MOBILE = (getattr(request, 'MOBILE', False) or
                          bool(request.COOKIES.get('mobile', False)))
