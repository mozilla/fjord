from django.db import models

from fjord.base.models import ModelBase, JSONObjectField


class Survey(ModelBase):
    """Defines a survey

    We'll create a survey every time we want to ask a new question to
    users. The survey name will be used in incoming answers posted by
    the heartbeat client.

    We won't capture answers for surveys that don't exist or are
    disabled.

    """
    name = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s: %s' % (
            self.slug, 'enabled' if self.enabled else 'disabled')


class Answer(ModelBase):
    """A survey answer.

    When a user is selected to be asked a survey question, we'll
    capture their answer, contextual data and their progression
    through the survey flow in an Answer.

    .. Note::

       This data contains personally identifiable information and so
       it can **never** be made publicly available.

    """
    # The version of the HTTP POST packet shape. This allows us to
    # change how some of the values in the packet are calculated and
    # distinguish between different iterations of answers for the same
    # survey.
    response_version = models.IntegerField()

    # Timestamp of the last update to this Answer.
    updated_ts = models.PositiveIntegerField()

    # uuids of things. person_id can have multiple flows where each
    # flow represents a different time the person was asked to
    # participate in the survey. It's possible the question text could
    # change. We capture it here to make it easier to do db analysis
    # without requiring extra maintenance (e.g. updating a Question
    # table).
    person_id = models.CharField(max_length=50)
    survey_id = models.ForeignKey(Survey, to_field='name', db_index=True)
    flow_id = models.CharField(max_length=50)
    question_id = models.CharField(max_length=50)
    question_text = models.TextField(blank=True)
    variation_id = models.CharField(max_length=50, blank=True)

    # score out of max_score.
    score = models.FloatField()
    max_score = models.FloatField()

    # These are the timestamps the user performed various actions in
    # the flow.
    flow_began_ts = models.PositiveIntegerField()
    flow_offered_ts = models.PositiveIntegerField()
    flow_voted_ts = models.PositiveIntegerField()
    flow_engaged_ts = models.PositiveIntegerField()

    # Data about the user's browser.
    platform = models.CharField(max_length=50, blank=True)
    channel = models.CharField(max_length=50, blank=True)
    version = models.CharField(max_length=50, blank=True)
    locale = models.CharField(max_length=50, blank=True)
    build_id = models.CharField(max_length=50, blank=True)
    partner_id = models.CharField(max_length=50, blank=True)

    # Data about the user's profile.
    profile_age = models.PositiveIntegerField()
    profile_usage = JSONObjectField()
    addons = JSONObjectField()

    # Whether or not this is test data.
    is_test = models.BooleanField(default=False)

    # This will likely include data like "crashiness", "search
    # settings" and any "weird settings". This will have some context
    # surrounding the rating score.
    slop = JSONObjectField()

    def __unicode__(self):
        return '%s: %s %s %s' % (
            self.id, self.surveyid, self.flowid, self.ts_updated)
