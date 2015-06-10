import logging

from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.cache import never_cache

from fjord.redirector import get_redirectors


logger = logging.getLogger('i.redirector')


# Note: We never want to cache redirects. This allows redirectors to
# capture correct metrics. At some point, we could make this optional
# on a redirector-to-redirector basis, but there's no need for that,
# yet.
@never_cache
def redirect_view(request):
    redirect = request.GET.get('r', None)
    if redirect is None:
        # No redirect data in the query params, so we return a 404.
        return HttpResponseNotFound('Not found')

    for prov in get_redirectors():
        try:
            url = prov.handle_redirect(request, redirect)
        except Exception:
            logger.exception('Error in provider {0}'.format(
                prov.__class__.__name__))

        if url is not None:
            return HttpResponseRedirect(url)

    # None of the providers handled the redirect, so we return
    # a 404.
    return HttpResponseNotFound('Not found')
