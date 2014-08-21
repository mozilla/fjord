from django.core.management.base import BaseCommand

from fjord.feedback.models import purge_data


class Command(BaseCommand):
    help = 'Purges old data'

    def handle(self, *args, **options):
        verbose = (int(options.get('verbosity', 1)) >= 1)
        purge_data(verbose=verbose)
