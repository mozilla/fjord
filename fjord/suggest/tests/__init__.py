from django.conf import settings

from fjord.base.plugin_utils import load_providers
from fjord.suggest import _SUGGESTERS


class SuggesterTestMixin(object):
    suggesters = settings.SUGGEST_PROVIDERS

    def setUp(self):
        super(SuggesterTestMixin, self).setUp()
        _SUGGESTERS[:] = load_providers(self.suggesters)

    def tearDown(self):
        super(SuggesterTestMixin, self).tearDown()
        _SUGGESTERS[:] = []
