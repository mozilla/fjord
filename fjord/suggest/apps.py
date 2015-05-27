import logging

from django.apps import AppConfig
from django.conf import settings

from fjord.base.plugin_utils import load_providers
from fjord.suggest import _SUGGESTERS


logger = logging.getLogger('i.suggest')


class SuggestConfig(AppConfig):
    name = 'fjord.suggest'

    def ready(self):
        # Load Suggesters and store them in _SUGGESTERS stomping on
        # whatever was there.
        _SUGGESTERS[:] = load_providers(settings.SUGGEST_PROVIDERS, logger)
