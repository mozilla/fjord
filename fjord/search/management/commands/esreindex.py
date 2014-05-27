import logging
from optparse import make_option
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError

from fjord.search.index import es_reindex_cmd


class Command(BaseCommand):
    help = dedent("""\
    Reindex the database for Elastic

    Use --percent=20 for criticalmass indexing.
    """)
    option_list = BaseCommand.option_list + (
        make_option('--percent', type='int', dest='percent', default=100,
                    help='Reindex a percentage of things'),
        make_option('--mappingtypes', type='string', dest='mappingtypes',
                    default=None,
                    help='Comma-separated list of mapping types to index'),
        )

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        es_logger = logging.getLogger('elasticsearch')
        es_logger.setLevel(logging.ERROR)

        percent = options['percent']
        mappingtypes = options['mappingtypes']
        if not 1 <= percent <= 100:
            raise CommandError('percent should be between 1 and 100')
        es_reindex_cmd(percent, mappingtypes)
