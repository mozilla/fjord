from django.core.management.base import BaseCommand

from fjord.base.utils import FakeLogger
from fjord.search.index import es_status_cmd


class Command(BaseCommand):
    help = 'Shows elastic search index status.'

    def handle(self, *args, **options):
        es_status_cmd(log=FakeLogger(self.stdout))
