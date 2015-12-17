from django.core.management.base import BaseCommand, CommandError

from fjord.heartbeat.healthchecks import run_healthchecks, email_healthchecks


class Command(BaseCommand):
    help = 'Runs heartbeat health checks and sends email'

    def handle(self, *args, **options):
        email_healthchecks(run_healthchecks())
        print 'Done!'
