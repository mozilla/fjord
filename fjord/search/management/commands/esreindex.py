import argparse
import logging
from textwrap import dedent

from django.core.management.base import BaseCommand

from fjord.search.index import es_reindex_cmd


def int_percent(value):
    value = int(value)
    if not 1 <= value <= 100:
        raise argparse.ArgumentTypeError('should be between 1 and 100')
    return value


class Command(BaseCommand):
    help = dedent("""\
    Reindex the database for Elasticsearch.

    Note: Use --percent=10 for criticalmass indexing.
    """)

    def add_arguments(self, parser):
        parser.add_argument(
            '--percent', type=int_percent, action='store', default=100,
            help='Reindex a percentage of things. Defaults to 100.'
        )
        parser.add_argument(
            '--doctypes', type=str, action='store',
            help='Comma-separated list of doctypes to index.'
        )

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        es_logger = logging.getLogger('elasticsearch')
        es_logger.setLevel(logging.ERROR)

        percent = options['percent']
        doctypes = options['doctypes']

        es_reindex_cmd(percent, doctypes)
