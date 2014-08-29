import json

from nose.tools import eq_

from fjord.base.tests import TestCase, reverse
from fjord.heartbeat.models import Answer
from fjord.heartbeat.tests import PollFactory


class HeartbeatPostAPITest(TestCase):
    def test_basic(self):
        poll = PollFactory.create()

        data = {
            'locale': 'es',
            'platform': 'Windows 8.1',
            'product': 'Firefox',
            'version': '30.0',
            'channel': 'stable',
            'poll': poll.slug,
            'answer': '0'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))
        eq_(resp.status_code, 201)

        ans = Answer.objects.latest('id')
        eq_(ans.locale, 'es')
        eq_(ans.platform, 'Windows 8.1')
        eq_(ans.product, 'Firefox')
        eq_(ans.version, '30.0')
        eq_(ans.channel, 'stable')
        eq_(ans.answer, '0')

    def test_missing_data(self):
        data = {}

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))
        eq_(resp.status_code, 400)

        json_data = json.loads(resp.content)
        eq_(json_data['msg'],
            'missing fields: answer, channel, locale, platform, poll, '
            'product, version')

        data = {
            'locale': 'es'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))
        eq_(resp.status_code, 400)

        json_data = json.loads(resp.content)
        eq_(json_data['msg'],
            'missing fields: answer, channel, platform, poll, '
            'product, version')

    def test_nonexistent_poll(self):
        data = {
            'locale': 'es',
            'platform': 'Windows 8.1',
            'product': 'Firefox',
            'version': '30.0',
            'channel': 'stable',
            'poll': 'badpoll',
            'answer': '0'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))
        eq_(resp.status_code, 400)
        eq_(resp.content,
            '{"msg": "poll \\"badpoll\\" does not exist"}')

    def test_disabled_poll(self):
        poll = PollFactory.create(enabled=False)

        data = {
            'locale': 'es',
            'platform': 'Windows 8.1',
            'product': 'Firefox',
            'version': '30.0',
            'channel': 'stable',
            'poll': poll.slug,
            'answer': '0'
        }

        resp = self.client.post(
            reverse('heartbeat-api'),
            content_type='application/json',
            data=json.dumps(data))
        eq_(resp.status_code, 400)
        eq_(resp.content,
            '{"msg": "poll \\"firefox-is-great\\" is not currently running"}')
