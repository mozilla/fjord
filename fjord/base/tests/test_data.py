from fjord.base.data import purge_data
from fjord.base.tests import TestCase
from fjord.journal.models import Record


class PurgeTestCase(TestCase):
    def test_purge_data_generates_journal_record(self):
        purge_data()
        assert Record.objects.filter(action='purge_data').count() == 1
