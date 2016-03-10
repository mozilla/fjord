from django.core import mail

from fjord.base.tests import TestCase
from fjord.heartbeat.healthcheck import (
    CheckAnyAnswers,
    CheckMissingVotes,
    email_healthchecks,
    MAILINGLIST,
    run_healthchecks,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
)
from fjord.heartbeat.tests import AnswerFactory, SurveyFactory
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


class TestCheckMissingVotesChecks(TestCase):
    def create_answers(self, number, score):
        survey = SurveyFactory.create(name='heartbeat-by-user-first-impression')
        AnswerFactory.create_batch(
            number,
            score=score,
            locale='en-us',
            survey_id=survey
        )

    def test_no_null_results(self):
        """No votes with null scores is fine."""
        self.create_answers(2, score=3)
        result = CheckMissingVotes.check()
        assert result.severity == SEVERITY_LOW
        assert result.summary == 'Data looks ok.'

    def test_few_null_results(self):
        """Less than 50 votes with null scores is fine."""
        self.create_answers(49, score=None)
        result = CheckMissingVotes.check()
        assert result.severity == SEVERITY_LOW
        assert result.summary == 'Data looks ok.'

    def test_many_null_results(self):
        """Between 50 and 250 null scores is medium severity."""
        self.create_answers(249, score=None)
        result = CheckMissingVotes.check()
        assert result.severity == SEVERITY_MEDIUM
        assert result.summary == '249 null votes within the last day.'

    def test_too_many_null_results(self):
        """250 or more null scores is high severity."""
        self.create_answers(300, score=None)
        result = CheckMissingVotes.check()
        assert result.severity == SEVERITY_HIGH
        assert result.summary == '300 null votes within the last day.'


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
