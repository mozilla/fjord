import time

import factory

from fjord.heartbeat.models import Answer, Survey


class SurveyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Survey

    name = 'survey123'
    enabled = True


class AnswerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Answer

    experiment_version = '1'
    response_version = 1
    updated_ts = int(time.time())
    survey_id = factory.SubFactory(SurveyFactory)
    flow_id = 'flowabc'
    question_id = 'questionabc'

    # The rest of the fields aren't required and should have sane
    # defaults.
