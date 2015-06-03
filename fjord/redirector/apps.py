import logging

from django.apps import AppConfig
from django.conf import settings

from fjord.base.plugin_utils import load_providers
from fjord.redirector import _REDIRECTORS


logger = logging.getLogger('i.redirector')


class RedirectorConfig(AppConfig):
    name = 'fjord.redirector'

    def ready(self):
        # Load providers and store them in _REDIRECTORS stomping on
        # whatever was there.
        _REDIRECTORS[:] = load_providers(settings.REDIRECTOR_PROVIDERS, logger)
