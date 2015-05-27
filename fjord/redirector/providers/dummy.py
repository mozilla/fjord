from fjord.redirector import Redirector


class DummyRedirector(Redirector):
    def handle_redirect(self, request, redirect):
        if redirect.startswith('dummy:'):
            redirect = redirect.split(':')
            return 'http://example.com/' + redirect[1]
        return
