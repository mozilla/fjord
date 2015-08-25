import urllib

from fjord.base.urlresolvers import reverse


class RedirectParseError(Exception):
    """Exception for when a redirect link doesn't parse"""
    pass


class Redirector(object):
    def load(self):
        """Implement this to perform any startup work"""
        pass

    def handle_redirect(self, request, redirect):
        """Implement this to handle redirects for a given request

        :returns: None or url to redirect to

        """
        raise NotImplementedError


def build_redirect_url(redirect):
    return reverse('redirect-view') + '?' + urllib.urlencode({'r': redirect})
