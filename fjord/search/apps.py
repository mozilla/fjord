from django.apps import AppConfig
from django.conf import settings

from elasticsearch_dsl.connections import connections


DEFAULT_URLS = ['localhost']
DEFAULT_TIMEOUT = 5


class SearchConfig(AppConfig):
    name = 'fjord.search'

    def ready(self):
        # Set up Elasticsearch connections based on settings
        urls = getattr(settings, 'ES_URLS', DEFAULT_URLS)
        timeout = getattr(settings, 'ES_TIMEOUT', DEFAULT_TIMEOUT)

        connections.configure(default={'hosts': urls, 'timeout': timeout})
