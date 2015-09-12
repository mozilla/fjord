import json

from fjord.base.tests import (
    AnalyzerProfileFactory,
    LocalizingClient,
    TestCase,
    reverse,
)

from fjord.feedback.tests import ResponseFactory


class TestTriggerRuleMatchViewAPI(TestCase):
    client_class = LocalizingClient

    def test_not_logged_in(self):
        data = {}
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 403

    def test_empty_tr(self):
        feedback_responses = ResponseFactory.create_batch(5)

        jane = AnalyzerProfileFactory().user
        self.client_login_user(jane)

        data = {
            'locales': [],
            'products': [],
            'versions': [],
            'keywords': [],
            'url_exists': None
        }
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        # Note: This matches everything because it's an empty rule.
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [fr.id for fr in reversed(feedback_responses)]
        )

    def test_invalid_data(self):
        jane = AnalyzerProfileFactory().user
        self.client_login_user(jane)

        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data='[}'
        )
        assert resp.status_code == 400

    def test_locales(self):
        ResponseFactory(locale=u'fr')
        es_resp = ResponseFactory(locale=u'es')
        enus_resp = ResponseFactory(locale=u'en-US')

        jane = AnalyzerProfileFactory().user
        self.client_login_user(jane)

        # Test one locale
        data = {
            'locales': [u'en-US'],
            'products': [],
            'versions': [],
            'keywords': [],
            'url_exists': None
        }
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [enus_resp.id]
        )

        # Test two
        data['locales'] = [u'en-US', u'es']
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [enus_resp.id, es_resp.id]
        )

    def test_products(self):
        fx_resp = ResponseFactory(product=u'Firefox')
        fxa_resp = ResponseFactory(product=u'Firefox for Android')
        ResponseFactory(product=u'Loop')

        jane = AnalyzerProfileFactory().user
        self.client_login_user(jane)

        # Test one product
        data = {
            'locales': [],
            'products': [u'Firefox'],
            'versions': [],
            'keywords': [],
            'url_exists': None
        }
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [fx_resp.id]
        )

        # Test two
        data['products'] = [u'Firefox', u'Firefox for Android']
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [fxa_resp.id, fx_resp.id]
        )

    def test_versions(self):
        te_resp = ResponseFactory(version=u'38.0')
        teof_resp = ResponseFactory(version=u'38.0.5')
        ResponseFactory(version=u'39.0')

        jane = AnalyzerProfileFactory().user
        self.client_login_user(jane)

        # Test one version
        data = {
            'locales': [],
            'products': [],
            'versions': [u'38.0'],
            'keywords': [],
            'url_exists': None
        }
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [te_resp.id]
        )

        # Test two
        data['versions'] = [u'38.0', u'38.0.5']
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [teof_resp.id, te_resp.id]
        )

        # Test prefix
        data['versions'] = [u'38*']
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [teof_resp.id, te_resp.id]
        )

    def test_keywords(self):
        rte_resp = ResponseFactory(description=u'Ride the lightning')
        fwtbt_resp = ResponseFactory(description=u'For whom the bell tolls')
        ResponseFactory(description=u'The thing that should not be')

        jane = AnalyzerProfileFactory().user
        self.client_login_user(jane)

        # Test one keyword
        data = {
            'locales': [],
            'products': [],
            'versions': [],
            'keywords': [u'lightning'],
            'url_exists': None
        }
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [rte_resp.id]
        )

        # Test two
        data['keywords'] = [u'lightning', u'tolls']
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [fwtbt_resp.id, rte_resp.id]
        )

        # Test phrase
        data['keywords'] = [u'bell tolls']
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [fwtbt_resp.id]
        )

    def test_url_exists(self):
        fb1 = ResponseFactory(url=u'')
        fb2 = ResponseFactory(url=u'http://example.com')
        fb3 = ResponseFactory(url=u'http://example.com')

        jane = AnalyzerProfileFactory().user
        self.client_login_user(jane)

        # Test don't care
        data = {
            'locales': [],
            'products': [],
            'versions': [],
            'keywords': [],
            'url_exists': None
        }
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [fb3.id, fb2.id, fb1.id]
        )

        # Test has a url
        data['url_exists'] = True
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [fb3.id, fb2.id]
        )

        # Test does not have a url
        data['url_exists'] = False
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        assert (
            [item['id'] for item in json.loads(resp.content)['results']] ==
            [fb1.id]
        )

    def test_contents(self):
        fr = ResponseFactory()

        jane = AnalyzerProfileFactory().user
        self.client_login_user(jane)

        data = {
            'locales': [],
            'products': [],
            'versions': [],
            'keywords': [],
            'url_exists': None
        }
        resp = self.client.post(
            reverse('triggerrule-match'),
            content_type='application/json',
            data=json.dumps(data)
        )
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert (
            content['results'] ==
            [
                {
                    u'id': int(fr.id),
                    u'created': fr.created.strftime(u'%Y-%m-%dT%H:%M:%S'),
                    u'description': fr.description,
                    u'happy': fr.happy,
                    u'locale': fr.locale,
                    u'product': fr.product,
                    u'platform': fr.platform,
                    u'url': fr.url,
                    u'version': fr.version
                }
            ]
        )
