from fjord.base.tests import reverse, TestCase
from fjord.redirector import get_redirectors
from fjord.redirector.base import build_redirect_url
from fjord.redirector.providers.dummy import DummyRedirector
from fjord.redirector.tests import RedirectorTestMixin


class DummyRedirectorLoadingTestCase(RedirectorTestMixin, TestCase):
    redirectors = []

    def test_didnt_load(self):
        dummy_providers = [
            prov for prov in get_redirectors()
            if isinstance(prov, DummyRedirector)
        ]
        assert len(dummy_providers) == 0


class DummyRedirectorTestCase(RedirectorTestMixin, TestCase):
    redirectors = [
        'fjord.redirector.providers.dummy.DummyRedirector'
    ]

    def test_load(self):
        dummy_redirectors = [
            prov for prov in get_redirectors()
            if isinstance(prov, DummyRedirector)
        ]
        assert len(dummy_redirectors) == 1

    def test_handle_redirect(self):
        resp = self.client.get(build_redirect_url('dummy:ou812'))
        assert resp.status_code == 302
        assert resp['Location'] == 'http://example.com/ou812'

    def test_nothing_handled_it_404(self):
        resp = self.client.get(build_redirect_url('notdummy:ou812'))
        assert resp.status_code == 404

    def test_no_redirect_specified_404(self):
        resp = self.client.get(reverse('redirect-view'))
        assert resp.status_code == 404
