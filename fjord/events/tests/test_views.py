import json

from fjord.base.tests import TestCase, reverse


class TestEventAPI(TestCase):
    def test_root(self):
        resp = self.client.get(reverse('event-api'))
        json_data = json.loads(resp.content)

        assert json_data['count'] > 0

    def test_products_filter(self):
        resp = self.client.get(reverse('event-api'))
        json_data = json.loads(resp.content)

        total_count = json_data['count']

        resp = self.client.get(reverse('event-api') + '?products=Firefox')
        json_data = json.loads(resp.content)

        assert total_count > json_data['count']

    def test_date_start_filter(self):
        resp = self.client.get(reverse('event-api'))
        json_data = json.loads(resp.content)

        total_count = json_data['count']

        resp = self.client.get(reverse('event-api') + '?date_start=2014-09-01')
        json_data = json.loads(resp.content)

        assert total_count > json_data['count']

    def test_date_end_filter(self):
        resp = self.client.get(reverse('event-api'))
        json_data = json.loads(resp.content)

        total_count = json_data['count']

        resp = self.client.get(reverse('event-api') + '?date_end=2013-09-01')
        json_data = json.loads(resp.content)

        assert total_count > json_data['count']

    def test_invalid_date(self):
        # FIXME: we should validate dates and then this would raise an
        # error
        resp = self.client.get(reverse('event-api') + '?date_start=omg')
        json_data = json.loads(resp.content)

        assert json_data['count'] == 0

    def test_nonexistent_product(self):
        # FIXME: we should validate product names and then this would
        # raise an error
        resp = self.client.get(reverse('event-api') + '?products=foo')
        json_data = json.loads(resp.content)

        assert json_data['count'] == 0
