from django.conf import settings

from fjord.base.plugin_utils import load_providers
from fjord.base.tests import TestCase
from fjord.suggest import _PROVIDERS


class ProviderTestCase(TestCase):
    providers = settings.SUGGEST_PROVIDERS

    def setUp(self):
        super(ProviderTestCase, self).setUp()
        _PROVIDERS[:] = load_providers(self.providers)

    def tearDown(self):
        super(ProviderTestCase, self).tearDown()
        _PROVIDERS[:] = []
