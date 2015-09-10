from fjord.base.tests import (
    AnalyzerProfileFactory,
    LocalizingClient,
    reverse,
    TestCase
)
from fjord.heartbeat.api_views import log_error
from fjord.heartbeat.tests import AnswerFactory, SurveyFactory


class HeartbeatHBDataTestCase(TestCase):
    client_class = LocalizingClient

    def test_permissions_and_basic_view(self):
        """Verify only analyzers can see hb_data view and view shows answers"""
        answer = AnswerFactory(flow_id='rehanrocks')

        resp = self.client.get(reverse('hb_data'))
        assert resp.status_code == 403

        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        resp = self.client.get(reverse('hb_data'))
        assert resp.status_code == 200
        assert answer.flow_id in resp.content


class HeartbeatHBErrorLogTestCase(TestCase):
    client_class = LocalizingClient

    def test_permissions_and_basic_view(self):
        """Verify only analyzers can see hb_errorlog view"""
        log_error({}, {'rehanrocks': 'really'})

        resp = self.client.get(reverse('hb_errorlog'))
        assert resp.status_code == 403

        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        resp = self.client.get(reverse('hb_errorlog'))
        assert resp.status_code == 200
        assert 'rehanrocks' in resp.content


class HeartbeatSurveysTestCase(TestCase):
    client_class = LocalizingClient

    def test_permissions_and_basic_view(self):
        """Verify only analyzers can see hb_surveys view"""
        resp = self.client.get(reverse('hb_surveys'))
        assert resp.status_code == 403

        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        resp = self.client.get(reverse('hb_surveys'))
        assert resp.status_code == 200

    def test_create_survey(self):
        # Create a survey and make sure it's there
        data = {
            'name': 'rehanrocks',
            'description': 'foo',
            'enabled': True
        }

        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        resp = self.client.post(reverse('hb_surveys'), data)
        assert resp.status_code == 302

        # Make sure it's in the survey list
        resp = self.client.get(reverse('hb_surveys'))
        assert resp.status_code == 200
        assert data['name'] in resp.content

    def test_update_survey(self):
        survey = SurveyFactory()

        data = {
            'id': survey.id,
            'name': 'rehanrocks',
            'description': survey.description,
            'enabled': survey.enabled
        }

        resp = self.client.post(
            reverse('hb_surveys_update', args=(survey.id,)),
            data
        )
        assert resp.status_code == 403

        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        resp = self.client.post(
            reverse('hb_surveys_update', args=(survey.id,)),
            data
        )
        assert resp.status_code == 302

        # Make sure it's in the survey list
        resp = self.client.get(reverse('hb_surveys'))
        assert resp.status_code == 200
        assert data['name'] in resp.content
