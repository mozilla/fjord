from textwrap import dedent

from fjord.base.tests import TestCase
from fjord.mailinglist.tests import MailingListFactory


class TestMailingList(TestCase):
    def test_recipients_empty(self):
        ml = MailingListFactory(members=u'')
        assert ml.recipient_list == []

    def test_recipients_whitespace(self):
        ml = MailingListFactory(members=u'  \n  ')
        assert ml.recipient_list == []

    def test_recipients_members(self):
        ml = MailingListFactory(members=u'foo@example.com\nbar@example.com')
        assert ml.recipient_list == [u'bar@example.com', u'foo@example.com']

    def test_recipients_complex(self):
        ml = MailingListFactory(
            members=dedent("""
            # foo
            foo@example.com

            # bar
            bar@example.com

            baz@example.com  # baz is awesome
            """)
        )
        assert (
            ml.recipient_list ==
            [u'bar@example.com', u'baz@example.com', u'foo@example.com']
        )
