from django.core.management.base import BaseCommand

from fjord.translations.models import get_translation_systems


class Command(BaseCommand):
    help = 'Runs translation-service daily activities.'

    def handle(self, *args, **options):
        verbose = (int(options.get('verbosity', 1)) >= 1)
        system_classes = get_translation_systems().values()

        for system_cls in system_classes:
            if not system_cls.use_daily:
                continue

            system = system_cls()

            if verbose:
                print '>>> {0} translation system'.format(system.name)
            system.run_daily_activities()

        if verbose:
            print '>>> Done!'
