from StringIO import StringIO
from django.core import management

from fjord.base.tests import TestCase


class TestExtract(TestCase):
    def test_help(self):
        try:
            management.call_command('extract', '--help')
        except SystemExit:
            # Calling --help causes it to call sys.exit(0) which
            # will otherwise exit.
            pass


class TestMerge(TestCase):
    def test_help(self):
        try:
            management.call_command('merge', '--help')
        except SystemExit:
            # Calling --help causes it to call sys.exit(0) which
            # will otherwise exit.
            pass
