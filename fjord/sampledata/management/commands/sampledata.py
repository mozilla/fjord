from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.importlib import import_module


class Command(BaseCommand):
    help = 'Loads sample data--helpful for development.'

    def handle(self, *args, **options):
        if not args:
            args = []

        for app in settings.INSTALLED_APPS:
            if args and app not in args:
                continue

            try:
                module = import_module('%s.sampledata' % app)
                if hasattr(module, 'generate_sampledata'):
                    print 'Loading sample data from %s...' % app
                    module.generate_sampledata()
            except ImportError:
                pass
        print 'Done!'
