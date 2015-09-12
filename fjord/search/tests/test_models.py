from fjord.base.tests import TestCase
from fjord.search.models import Record
from fjord.search.tests import RecordFactory


class TestRecord(TestCase):
    def test_mark(self):
        """Test marking as fail/success."""
        r = RecordFactory()

        assert Record.objects.filter(status=Record.STATUS_NEW).count() == 1
        assert Record.objects.filter(status=Record.STATUS_FAIL).count() == 0
        assert Record.objects.filter(status=Record.STATUS_SUCCESS).count() == 0

        r.mark_fail('Errorz!')
        assert Record.objects.filter(status=Record.STATUS_NEW).count() == 0
        assert Record.objects.filter(status=Record.STATUS_FAIL).count() == 1
        assert Record.objects.filter(status=Record.STATUS_SUCCESS).count() == 0

        r.mark_success()
        assert Record.objects.filter(status=Record.STATUS_NEW).count() == 0
        assert Record.objects.filter(status=Record.STATUS_FAIL).count() == 0
        assert Record.objects.filter(status=Record.STATUS_SUCCESS).count() == 1
