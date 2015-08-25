import json
import time

from . import SurveyFactory
from ..models import Answer
from fjord.base.tests import TestCase, reverse
from fjord.journal.models import Record


class HeartbeatPostAPITest(TestCase):
    _base_ts = time.time()

    def timestamp(self, offset=0):
        """Returns time since epoch in milliseconds

        This uses a instance property to maintain a base ts from which
        all offsets are generated. This makes it easier to write tests
        that require timestamps within specific distances from one
        another.

        """
        return int(self._base_ts + offset) * 1000

    def test_minimal_data(self):
        """Minimum amount of data required"""
        survey = SurveyFactory.create()
        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),
            'question_text': 'how was lunch?',
            'variation_id': '1'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 201

    def test_initial_answer(self):
        """Initial answer using "non values" for many fields"""
        survey = SurveyFactory.create()

        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),

            'question_text': 'ou812?',
            'variation_id': '1',
            'score': None,
            'max_score': None,
            'flow_began_ts': 0,
            'flow_offered_ts': 0,
            'flow_voted_ts': 0,
            'flow_engaged_ts': 0,
            'platform': '',
            'channel': '',
            'version': '',
            'locale': '',
            'country': '',
            'build_id': '',
            'partner_id': '',
            'profile_age': None,
            'profile_usage': {},
            'addons': {},
            'extra': {},
            'is_test': False
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 201

        ans = Answer.objects.latest('id')

        for field in data.keys():
            # survey_id is a special case since it's a foreign key.
            if field == 'survey_id':
                # This looks goofy because it's not the normal way to
                # do things, but the "survey_id" attribute is a
                # Survey rather than the pk for a Survey.
                assert ans.survey_id.name == data[field]
                continue

            assert getattr(ans, field) == data[field]

    def test_complete_answer(self):
        """Complete answer using sane values for everything"""
        survey = SurveyFactory.create()

        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),

            'question_text': 'ou812?',
            'variation_id': '1',
            'score': 5.0,
            'max_score': 1.0,
            'flow_began_ts': self.timestamp(offset=-40),
            'flow_offered_ts': self.timestamp(offset=-30),
            'flow_voted_ts': self.timestamp(offset=-20),
            'flow_engaged_ts': self.timestamp(offset=-10),
            'platform': 'Windows',
            'channel': 'stable',
            'version': '33.1',
            'locale': 'en-US',
            'country': 'US',
            'build_id': 'dd2f144cdf44',
            'partner_id': 'Phil',
            'profile_age': 365,
            'profile_usage': {'abc': 'def'},
            'addons': {'foo': 'bar'},
            'extra': {'baz': 'bat'}
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 201

        ans = Answer.objects.latest('id')

        for field in data.keys():
            # survey_id is a special case since it's a foreign key.
            if field == 'survey_id':
                # This looks goofy because it's not the normal way to
                # do things, but the "survey_id" attribute is a
                # Survey rather than the pk for a Survey.
                assert ans.survey_id.name == data[field]
                continue

            assert getattr(ans, field) == data[field]

        assert ans.is_test == False

    def test_country_unknown(self):
        """This is a stopgap fix for handling 'unknown' value for country"""
        survey = SurveyFactory.create()

        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),

            'question_text': 'ou812?',
            'variation_id': '1',
            'country': 'unknown'
        }
        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 201
        ans = Answer.objects.latest('id')
        assert ans.country == 'UNK'

    def test_survey_doesnt_exist(self):
        """If the survey doesn't exist, kick up an error"""
        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': 'foosurvey',
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),
            'question_text': 'how was lunch?',
            'variation_id': '1'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 400
        errors = json.loads(resp.content)['errors']
        assert (
            errors['survey_id'] ==
            [u'Object with name=foosurvey does not exist.']
            )

    def test_survey_disabled(self):
        """If the survey is disabled, kick up an error"""
        survey = SurveyFactory.create(enabled=False)

        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),
            'question_text': 'how was lunch?',
            'variation_id': '1'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 400
        errors = json.loads(resp.content)['errors']
        assert (
            errors['survey_id'] ==
            ['survey "%s" is not enabled' % survey.name]
            )

    def test_missing_data(self):
        """Missing required data kicks up an error"""
        survey = SurveyFactory.create()

        orig_data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),
            'question_text': 'how was lunch?',
            'variation_id': '1'
        }

        for key in orig_data.keys():
            data = dict(orig_data)
            del data[key]

            resp = self.client.post(
                reverse('heartbeat-api'),
                content_type='application/json',
                data=json.dumps(data))

            assert resp.status_code == 400
            resp_data = json.loads(resp.content)
            assert key in resp_data['errors']

    def test_error_logging(self):
        """Errors in the packet should be logged in the journal"""
        # Verify nothing in the journal
        assert len(Record.objects.recent('heartbeat')) == 0

        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': 'foosurvey',
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),
            'question_text': 'how was lunch?',
            'variation_id': '1'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 400
        errors = json.loads(resp.content)['errors']
        assert len(errors) > 0

        # Verify there's one entry now.
        assert len(Record.objects.recent('heartbeat')) == 1

    def test_updated_ts_greater(self):
        """If the updated_ts > existing, then update the Answer"""
        survey = SurveyFactory.create()

        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(offset=-10),
            'question_text': 'how was lunch?',
            'variation_id': '1'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 201

        # Make sure the answer made it to the db and that the data
        # matches.
        ans = Answer.objects.latest('id')
        assert ans.person_id ==  data['person_id']
        assert ans.survey_id.name == data['survey_id']
        assert ans.flow_id ==  data['flow_id']
        assert ans.question_id ==  data['question_id']
        assert ans.updated_ts ==  data['updated_ts']
        assert ans.question_text ==  data['question_text']
        assert ans.variation_id ==  data['variation_id']
        assert ans.score ==  None
        assert ans.max_score == None

        ans_id = ans.id

        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),
            'question_text': 'how was lunch?',
            'variation_id': '1',
            'score': 5.0,
            'max_score': 10.0
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 201

        ans = Answer.objects.get(id=ans_id)
        ans = Answer.objects.latest('id')
        assert ans.person_id == data['person_id']
        assert ans.survey_id.name == data['survey_id']
        assert ans.flow_id == data['flow_id']
        assert ans.question_id == data['question_id']
        assert ans.updated_ts == data['updated_ts']
        assert ans.question_text == data['question_text']
        assert ans.variation_id == data['variation_id']
        assert ans.score == 5.0
        assert ans.max_score == 10.0

    def test_updated_ts_lessthan_equal(self):
        """If the updated_ts <= existing, then update the Answer"""
        survey = SurveyFactory.create()

        data = {
            'experiment_version': '1',
            'response_version': 1,
            'person_id': 'joemamma',
            'survey_id': survey.name,
            'flow_id': '20141113',
            'question_id': '1',
            'updated_ts': self.timestamp(),
            'question_text': 'how was lunch?',
            'variation_id': '1',
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 201

        # Test the less-than case.
        data['updated_ts'] = self.timestamp(offset=-10)
        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 400
        resp_data = json.loads(resp.content)
        assert (
            resp_data['errors']['updated_ts'] ==
            'updated timestamp is same or older than existing data'
            )

        # Test the equal case.
        data['updated_ts'] = self.timestamp()
        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert resp.status_code == 400
        resp_data = json.loads(resp.content)
        assert (
            resp_data['errors']['updated_ts'] ==
            'updated timestamp is same or older than existing data'
            )

    def test_cors(self):
        """Verify the CORS headers in the OPTIONS response."""
        resp = self.client.options(
            reverse('heartbeat-api'),
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='')
        assert resp['Access-Control-Allow-Methods'] =='POST'
        assert resp['Access-Control-Allow-Origin'] == '*'

    # FIXME: test bad types and validation so we can suss out
    # exception handling issues
