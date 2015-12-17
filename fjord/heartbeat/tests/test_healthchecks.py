from django.core import mail

from fjord.base.tests import TestCase
from fjord.heartbeat.healthchecks import (
    CheckAnyAnswers,
    email_healthchecks,
    run_healthchecks,
    SEVERITY_LOW,
    SEVERITY_HIGH,
)
from fjord.heartbeat.tests import AnswerFactory, SurveyFactory
from fjord.mailinglist.tests import MailingListFactory


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
        email_healthchecks(run_healthchecks())
        assert len(mail.outbox) == 0
        # FIXME: test that something got logged?

    def test_with_recipients(self):
        """If there are recipients, then email is sent"""
        MailingListFactory(
            name='heartbeat_health',
            members=u'foo@example.com'
        )

        email_healthchecks(run_healthchecks())
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [u'foo@example.com']
        # Severity should be HIGH since there's no hb items--at least
        # one of the checks should be all like, "OMG! RED ALERT!"
        assert 'HIGH' in mail.outbox[0].subject
