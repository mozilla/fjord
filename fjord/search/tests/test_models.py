from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.search.models import Record
from fjord.search.tests import RecordFactory


class RecordTest(TestCase):
    def test_mark(self):
        """Test marking as fail/success."""
        r = RecordFactory()

        eq_(Record.objects.filter(status=Record.STATUS_NEW).count(), 1)
        eq_(Record.objects.filter(status=Record.STATUS_FAIL).count(), 0)
        eq_(Record.objects.filter(status=Record.STATUS_SUCCESS).count(), 0)

        r.mark_fail('Errorz!')
        eq_(Record.objects.filter(status=Record.STATUS_NEW).count(), 0)
        eq_(Record.objects.filter(status=Record.STATUS_FAIL).count(), 1)
        eq_(Record.objects.filter(status=Record.STATUS_SUCCESS).count(), 0)

        r.mark_success()
        eq_(Record.objects.filter(status=Record.STATUS_NEW).count(), 0)
        eq_(Record.objects.filter(status=Record.STATUS_FAIL).count(), 0)
        eq_(Record.objects.filter(status=Record.STATUS_SUCCESS).count(), 1)
