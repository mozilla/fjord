from django.core.management import call_command

from fjord.base.tests import TestCase


class TestGenerateData(TestCase):
    def test_generate_data(self):
        """Make sure ./manage.py generatedata runs."""
        call_command('generatedata')
        call_command('generatedata', bigsample=True)


class TestPOLint(TestCase):
    def test_polint(self):
        """Make sure ./manage.py polint runs."""
        # Note: This doesn't make sure it works--just that it doesn't kick
        # up obvious errors when it runs like if Dennis has changed in
        # some way that prevents it from working correctly.

        try:
            call_command('polint')
        except SystemExit:
            # WOAH! WTF ARE YOU DOING? The lint command calls
            # sys.exit() because it needs to return correct exit codes
            # so we catch that here and ignore it. Otherwise testing
            # it will kill the test suite.
            pass
