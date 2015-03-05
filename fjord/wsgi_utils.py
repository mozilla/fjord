from django.conf import settings


class BetterDebugMixin(object):
    """Provides better debugging data

    Developing API endpoints and tired of wading through HTML for HTTP
    500 errors?

    Working on POST API debugging and not seeing the POST data show up
    in the error logs/emails?

    Then this mixin is for you!

    It:

    * spits out text rather than html when DEBUG = True (OMG! THANK
      YOU!)
    * adds a "HTTP_X_POSTBODY" META variable so you can see the raw post
      data in error emails which is gross, but I couldn't figure out
      a better way to do it

    Usage:

    Create a WSGIHandler subclass and bind that to ``application`` in
    your wsgi file. For example::

        import django
        from django.core.handlers.wsgi import WSGIHandler

        from fjord.wsgi_utils import BetterDebugMixin


        class MyWSGIHandler(BetterDebugMixin, WSGIHandler):
            pass


        def get_debuggable_wsgi_application():
            # This does the same thing as
            # django.core.wsgi.get_wsgi_application except
            # it returns a different WSGIHandler.
            django.setup()
            return MyWSGIHandler()


        application = get_debuggable_wsgi_application()

    """
    def handle_uncaught_exception(self, request, resolver, exc_info):
        if settings.DEBUG_PROPAGATE_EXCEPTIONS:
            raise

        # First, grab the raw POST body and put it somewhere that's
        # guaranteed to show up in the error email.

        # This should be "bytes" which is str type in Python 2.
        #
        # FIXME: This is probably broken with Python 3.
        postbody = getattr(request, 'body', '')
        try:
            # For string-ish data, we truncate and decode/re-encode in
            # utf-8.
            postbody = postbody[:10000].decode('utf-8').encode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # For binary, we say, 'BINARY CONTENT'
            postbody = 'BINARY OR NON-UTF-8 CONTENT'
        except Exception as exc:
            postbody = 'Error figuring out postbody %r' % exc

        # The logger.error generates a record which can get handled by
        # the AdminEmailHandler. Overriding all that machinery is
        # daunting, so we're instead going to shove it in the META
        # section which shows up when the machinery does a repr on
        # WSGIRequest.
        request.META['HTTP_X_POST_BODY'] = postbody

        # Second, check the Accept header and if it's not text/html,
        # pretend this is an AJAX request so that we get the output in
        # text rather than html when DEBUG=True.
        if settings.DEBUG:
            # request.is_ajax() == True will push this into doing text
            # instead of html which is waaaaaayyy more useful from an
            # API perspective. So if the Accept header is anything other
            # than html, we'll say it's an ajax request to return text.
            if 'html' not in request.META.get('HTTP_ACCEPT', 'text/html'):
                request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        return super(BetterDebugMixin, self).handle_uncaught_exception(
            request, resolver, exc_info)
