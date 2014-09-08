import logging

from django.core.management.base import BaseCommand, CommandError

from fjord.flags.spicedham_utils import train_cmd


class Command(BaseCommand):
    help = ('Trains abuse classifier. Specify directory with abuse.json '
            'and nonabuse.json files.')

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        if not args:
            raise CommandError('You must specify directory with abuse/ham '
                               'corpuses.')

        train_cmd(args[0], classification='abuse')
