from django.db import models

from rest_framework import serializers

from fjord.base.api_utils import UTCDateTimeField
from fjord.base.models import ModelBase, JSONObjectField


class Survey(ModelBase):
    """Defines a survey

    We'll create a survey every time we want to ask a new question to
    users. The survey name will be used in incoming answers posted by
    the heartbeat client.

    We won't capture answers for surveys that don't exist or are
    disabled.

    """
    name = models.CharField(
        max_length=100, unique=True,
        help_text=u'Unique name for the survey. e.g. heartbeat-question-1'
    )
    description = models.TextField(
        blank=True, default='',
        help_text=(
            u'Informal description of the survey so we can tell them apart'
        )
    )
    enabled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s: %s' % (
            self.name, 'enabled' if self.enabled else 'disabled')


class Answer(ModelBase):
    """A survey answer.

    When a user is selected to be asked a survey question, we'll
    capture their answer, contextual data and their progression
    through the survey flow in an Answer.

    .. Note::

       This data contains personally identifiable information and so
       it can **never** be made publicly available.

    """
    # The version of the experiment addon.
    experiment_version = models.CharField(max_length=50)

    # The version of the HTTP POST packet shape. This allows us to
    # change how some of the values in the packet are calculated and
    # distinguish between different iterations of answers for the same
    # survey.
    response_version = models.IntegerField()

    # Timestamp of the last update to this Answer.
    updated_ts = models.BigIntegerField(default=0)

    # uuids of things. person_id can have multiple flows where each
    # flow represents a different time the person was asked to
    # participate in the survey. It's possible the question text could
    # change. We capture it here to make it easier to do db analysis
    # without requiring extra maintenance (e.g. updating a Question
    # table).
    person_id = models.CharField(max_length=50)
    survey_id = models.ForeignKey(
        Survey, db_column='survey_id', to_field='name', db_index=True)
    flow_id = models.CharField(max_length=50)

    # The id, text and variation of the question being asked.
    question_id = models.CharField(max_length=50)
    question_text = models.TextField()
    variation_id = models.CharField(max_length=100)

    # score out of max_score. Use null for no value.
    score = models.FloatField(null=True, blank=True)
    max_score = models.FloatField(null=True, blank=True)

    # These are the timestamps the user performed various actions in
    # the flow. Use 0 for no value.
    flow_began_ts = models.BigIntegerField(default=0)
    flow_offered_ts = models.BigIntegerField(default=0)
    flow_voted_ts = models.BigIntegerField(default=0)
    flow_engaged_ts = models.BigIntegerField(default=0)

    # Data about the user's browser. Use '' for no value.
    platform = models.CharField(max_length=50, blank=True, default=u'')
    channel = models.CharField(max_length=50, blank=True, default=u'')
    version = models.CharField(max_length=50, blank=True, default=u'')
    locale = models.CharField(max_length=50, blank=True, default=u'')
    country = models.CharField(max_length=4, blank=True, null=True,
                               default=u'')
    build_id = models.CharField(max_length=50, blank=True, default=u'')
    partner_id = models.CharField(max_length=50, blank=True, default=u'')

    # Data about the user's profile. Use null for no value.
    profile_age = models.BigIntegerField(null=True, blank=True)

    # Data about the profile usage, addons and extra stuff. Use {} for
    # no value.
    profile_usage = JSONObjectField(blank=True)
    addons = JSONObjectField(blank=True)

    # This will likely include data like "crashiness", "search
    # settings" and any "weird settings". This will have some context
    # surrounding the rating score.
    extra = JSONObjectField(blank=True)

    # Whether or not this is test data.
    is_test = models.BooleanField(default=False, blank=True)

    received_ts = models.DateTimeField(
        auto_now=True,
        help_text=u'Time the server received the last update packet')

    class Meta:
        unique_together = (
            ('person_id', 'survey_id', 'flow_id'),
        )
        index_together = [
            ('person_id', 'survey_id', 'flow_id'),
        ]

    def __unicode__(self):
        return '%s: %s %s %s' % (
            self.id, self.survey_id, self.flow_id, self.updated_ts)


class AnswerSerializer(serializers.ModelSerializer):
    updated_ts = serializers.IntegerField(required=True)
    survey_id = serializers.SlugRelatedField(
        queryset=Survey.objects.all(), slug_field='name')

    received_ts = UTCDateTimeField(read_only=True)

    class Meta:
        model = Answer

    def validate_survey_id(self, survey):
        # Make sure the survey is enabled--otherwise error out.
        if not survey.enabled:
            raise serializers.ValidationError(
                'survey "%s" is not enabled' % survey.name)
        return survey

    def get_unique_together_validators(self):
        # We no-op this because we want to ignore the unique fields
        # check on the model instance so that we can "update on
        # POST". We do "update on POST" in order to simplify the
        # heartbeat client.
        return []
