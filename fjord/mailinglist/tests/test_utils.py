from fjord.base.tests import TestCase
from fjord.mailinglist.tests import MailingListFactory
from fjord.mailinglist.utils import get_recipients


class TestGetRecipients(TestCase):
    def test_doesnt_exist(self):
        """Getting recipients from a non-existent mailing list is an empty list
        """
        assert get_recipients('foo') == []

    def test_no_members(self):
        ml = MailingListFactory(members=u'')
        assert get_recipients(ml.name) == []

    def test_has_members(self):
        ml = MailingListFactory(members=u'foo@example.com\nbar@example.com')
        assert (
            get_recipients(ml.name) ==
            ['bar@example.com', 'foo@example.com']
        )
