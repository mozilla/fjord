from datetime import datetime, timedelta

from fjord.base.tests import TestCase
from fjord.journal.models import purge_data, Record
from fjord.journal.tests import RecordFactory


class TestPurgeData(TestCase):
    def test_purge(self):
        now = datetime.now()

        # Create three journal records
        record_a = RecordFactory(created=now - timedelta(days=5))
        RecordFactory(created=now - timedelta(days=181))
        RecordFactory(created=now - timedelta(days=200))

        assert Record.objects.count() == 3
        purge_data()
        assert Record.objects.count() == 1
        assert Record.objects.values_list('id', flat=True)[0] == record_a.id
