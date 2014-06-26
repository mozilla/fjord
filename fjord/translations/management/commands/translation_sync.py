from django.core.management.base import BaseCommand

from fjord.translations.models import get_translation_systems


class Command(BaseCommand):
    help = 'Syncs translations with all translation systems.'

    def handle(self, *args, **options):
        system_classes = get_translation_systems().values()

        for system_cls in system_classes:
            system = system_cls()
            print '>>> {0} translation system'.format(system.name)
            print 'Pulling...'
            system.pull_translations()
            print 'Pushing...'
            system.push_translations()

        print '>>> Done!'
