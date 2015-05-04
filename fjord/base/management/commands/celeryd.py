"""

Start the celery daemon from the Django management command.

"""
from __future__ import absolute_import, unicode_literals

import os
import sys

from django.core.management.base import BaseCommand

import celery
from celery.bin.worker import worker as WorkerCommand

from fjord.celery import app


worker = WorkerCommand(app=app)


# This code is based on django-celery code. It's a merge of
# djcelery.management.base.CeleryCommand and
# djcelery.management.commands.celeryd.Command.
class Command(BaseCommand):
    help = 'Old alias to the "celery worker" command.'
    options = (BaseCommand.option_list
               + worker.get_options()
               + worker.preload_options)
    skip_opts = ['--app', '--loader', '--config', '--no-color']
    requires_model_validation = False
    keep_base_opts = False
    stdout, stderr = sys.stdout, sys.stderr

    def handle(self, *args, **options):
        worker.check_args(args)
        worker.run(**options)

    def get_version(self):
        return 'celery {c.__version__}'.format(c=celery)

    def execute(self, *args, **options):
        broker = options.get('broker')
        if broker:
            self.set_broker(broker)
        super(Command, self).execute(*args, **options)

    def set_broker(self, broker):
        os.environ['CELERY_BROKER_URL'] = broker

    def run_from_argv(self, argv):
        self.handle_default_options(argv[2:])
        return super(Command, self).run_from_argv(argv)

    def handle_default_options(self, argv):
        acc = []
        broker = None
        for i, arg in enumerate(argv):
            # --settings and --pythonpath are also handled
            # by BaseCommand.handle_default_options, but that is
            # called with the resulting options parsed by optparse.
            if '--settings=' in arg:
                _, settings_module = arg.split('=')
                os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
            elif '--pythonpath=' in arg:
                _, pythonpath = arg.split('=')
                sys.path.insert(0, pythonpath)
            elif '--broker=' in arg:
                _, broker = arg.split('=')
            elif arg == '-b':
                broker = argv[i + 1]
            else:
                acc.append(arg)
        if broker:
            self.set_broker(broker)
        return argv if self.keep_base_opts else acc

    def die(self, msg):
        sys.stderr.write(msg)
        sys.stderr.write('\n')
        sys.exit()

    def _is_unwanted_option(self, option):
        return option._long_opts and option._long_opts[0] in self.skip_opts

    @property
    def option_list(self):
        return [x for x in self.options if not self._is_unwanted_option(x)]
