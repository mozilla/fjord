import random
from uuid import uuid4

from fjord.heartbeat.tests import SurveyFactory, AnswerFactory


def generate_sampledata(options):
    survey = SurveyFactory(
        name=u'Sample survey ' + str(uuid4()),
        description=u'This is a sample survey.',
        enabled=True
    )

    # Add some "real data"
    for i in range(10):
        AnswerFactory(
            person_id=str(uuid4()),
            survey_id=survey,
            score=random.randint(1, 5),
            max_score=5
        )

    # Add a test data item
    AnswerFactory(
        person_id=str(uuid4()),
        survey_id=survey,
        score=3,
        max_score=5,
        is_test=True
    )

    print 'Done!'
