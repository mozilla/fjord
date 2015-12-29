import time

import factory
from factory import fuzzy

from fjord.heartbeat.models import Answer, Survey


class SurveyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Survey

    name = fuzzy.FuzzyText(length=100)
    enabled = True


class AnswerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Answer

    experiment_version = '1'
    response_version = 1
    updated_ts = int(time.time())
    survey_id = factory.SubFactory(SurveyFactory)
    flow_id = fuzzy.FuzzyText(length=50)
    question_id = fuzzy.FuzzyText(length=50)

    # The rest of the fields aren't required and should have sane
    # defaults.
