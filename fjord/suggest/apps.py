import logging

from django.apps import AppConfig
from django.conf import settings

from fjord.suggest import _PROVIDERS
from fjord.base.plugin_utils import load_providers


logger = logging.getLogger('i.suggest')


class SuggestConfig(AppConfig):
    name = 'fjord.suggest'

    def ready(self):
        # Load providers and store them in _PROVIDERS stomping on
        # whatever was there.
        _PROVIDERS[:] = load_providers(settings.SUGGEST_PROVIDERS, logger)
