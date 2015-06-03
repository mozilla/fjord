import logging

from django.http import HttpResponseNotFound, HttpResponseRedirect

from fjord.redirector import get_redirectors


logger = logging.getLogger('i.redirector')


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
