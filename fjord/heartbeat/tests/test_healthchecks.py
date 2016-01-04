from django.core import mail

from fjord.base.tests import TestCase
from fjord.heartbeat.healthcheck import (
    CheckAnyAnswers,
    email_healthchecks,
    MAILINGLIST,
    run_healthchecks,
    SEVERITY_LOW,
    SEVERITY_HIGH,
)
from fjord.heartbeat.tests import AnswerFactory
from fjord.mailinglist.models import MailingList


class TestCheckAnyAnswers(TestCase):
    def test_good(self):
        """One or more answers is fine"""
        AnswerFactory.create_batch(2)

        result = CheckAnyAnswers.check()
        assert result.severity == SEVERITY_LOW
        assert result.summary == '2 answers in last 24 hours.'
        assert result.output == '2'

    def test_bad(self):
        """No answers is very bad"""
        result = CheckAnyAnswers.check()
        assert result.severity == SEVERITY_HIGH
        assert result.summary == '0 answers in last 24 hours.'
        assert result.output == '0'


class TestRunHealthChecks(TestCase):
    def test_basic(self):
        results = run_healthchecks()
        # Note: You'll need to update this any time we add a health check.
        assert len(results) == 2


class TestEmailHealthChecks(TestCase):
    def test_no_recipients(self):
        """If there are no recipients, no email is sent"""
        # The mailing list gets created in data migrations. For the purposes of
        # this test, we delete that.
        MailingList.objects.filter(name=MAILINGLIST).delete()

        email_healthchecks(run_healthchecks())
        assert len(mail.outbox) == 0
        # FIXME: test that something got logged?

    def test_with_recipients(self):
        """If there are recipients, then email is sent"""
        # Note: The mailing list should get created in data migrations.
        ml = MailingList.objects.get(name=MAILINGLIST)
        ml.members = u'foo@example.com'
        ml.save()

        email_healthchecks(run_healthchecks())
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [u'foo@example.com']
        # Severity should be RED ALERT since there's no hb items--at least
        # one of the checks should be all like, "OMG! RED ALERT!"
        assert 'RED ALERT' in mail.outbox[0].subject
