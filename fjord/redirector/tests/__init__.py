from fjord.base.plugin_utils import load_providers
from fjord.redirector import _REDIRECTORS


class RedirectorTestMixin(object):
    """Mixin that loads Redirectors specified with ``redirectors`` attribute"""
    redirectors = []

    def setUp(self):
        _REDIRECTORS[:] = load_providers(self.redirectors)
        super(RedirectorTestMixin, self).setUp()

    def tearDown(self):
        _REDIRECTORS[:] = []
        super(RedirectorTestMixin, self).tearDown()
