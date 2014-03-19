from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from fjord.translations.models import get_translation_systems


class Command(BaseCommand):
    help = 'Syncs translations with implemented systems.'

    def handle(self, *args, **options):
        systems = getattr(settings, 'TRANSLATION_SYSTEMS_TO_SYNC', [])
        if not systems:
            raise CommandError(
                'No systems to sync. Set '
                'settings.TRANSLATION_SYSTEMS_TO_SYNC = [SYSTEMS]')

        all_systems = get_translation_systems()

        system_classes = []
        try:
            for key in systems:
                system_classes.append(all_systems[key])
        except KeyError:
            # FIXME - This is lazy error reporting. It should report
            # the system that
            raise CommandError(
                'System "{0}" does not exist. '
                'Existing systems are {0}.'.format(
                    key, all_systems.keys()))

        for system_cls in system_classes:
            system = system_cls()
            print '>>> {0} translation system'.format(system.name)
            print 'Pulling...'
            system.pull_translations()
            print 'Pushing...'
            system.push_translations()

        print '>>> Done!'
