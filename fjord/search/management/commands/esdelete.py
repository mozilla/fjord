import logging

from django.core.management.base import BaseCommand

from fjord.search.index import es_delete_cmd


class Command(BaseCommand):
    help = 'Delete an index from elastic search.'

    def add_arguments(self, parser):
        parser.add_argument('index', nargs=1)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)

        es_delete_cmd(options['index'][0])
