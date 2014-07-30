import json
from datetime import date, timedelta

from django.conf import settings
from django.test.client import Client

from nose.tools import eq_

from fjord.base.tests import TestCase, reverse
from fjord.feedback import models
from fjord.feedback.tests import ResponseFactory
from fjord.search.tests import ElasticTestCase


class PublicFeedbackAPITest(ElasticTestCase):
    def create_basic_data(self):
        testdata = [
            (True, 'en-US', 'Linux', 'Firefox', '30.0', 'desc'),
            (True, 'en-US', 'Mac OSX', 'Firefox for Android', '31.0', 'desc'),
            (False, 'de', 'Windows', 'Firefox', '29.0', 'banana'),
        ]

        for happy, locale, platform, product, version, desc in testdata:
            ResponseFactory(
                happy=happy, locale=locale, platform=platform,
                product=product, version=version, description=desc)
        self.refresh()

    def test_basic_root(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'))
        # FIXME: test headers
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 3)
        eq_(len(json_data['results']), 3)

    def test_happy(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'), {'happy': '1'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 2)
        eq_(len(json_data['results']), 2)

    def test_platforms(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'), {'platforms': 'Linux'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 1)
        eq_(len(json_data['results']), 1)

        resp = self.client.get(reverse('feedback-api'),
                               {'platforms': 'Linux,Windows'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 2)
        eq_(len(json_data['results']), 2)

    def test_products_and_versions(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'),
                               {'products': 'Firefox'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 2)
        eq_(len(json_data['results']), 2)

        resp = self.client.get(reverse('feedback-api'),
                               {'products': 'Firefox,Firefox for Android'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 3)
        eq_(len(json_data['results']), 3)

        # version without product gets ignored
        resp = self.client.get(reverse('feedback-api'),
                               {'versions': '30.0'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 3)
        eq_(len(json_data['results']), 3)

        resp = self.client.get(reverse('feedback-api'),
                               {'products': 'Firefox',
                                'versions': '30.0'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 1)
        eq_(len(json_data['results']), 1)

    def test_locales(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'), {'locales': 'en-US'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 2)
        eq_(len(json_data['results']), 2)

        resp = self.client.get(reverse('feedback-api'),
                               {'locales': 'en-US,de'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 3)
        eq_(len(json_data['results']), 3)

    def test_multi_filter(self):
        self.create_basic_data()

        # Locale and happy
        resp = self.client.get(reverse('feedback-api'), {
            'locales': 'de', 'happy': 1
        })
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 0)
        eq_(len(json_data['results']), 0)

    def test_query(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'), {'q': 'desc'})
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 2)
        eq_(len(json_data['results']), 2)

    def create_date_data(self):
        """Create and send test data"""
        testdata = [
            ('2014-07-01', True, 'en-US', 'Firefox'),
            ('2014-07-02', True, 'en-US', 'Firefox for Android'),
            ('2014-07-03', False, 'de', 'Firefox'),
            ('2014-07-04', False, 'de', 'Firefox for Android'),
        ]
        for date_start, happy, platform, product in testdata:
            ResponseFactory(
                happy=happy, platform=platform, product=product,
                created=date_start)
        self.refresh()

    def _test_date(self, getoptions, expectedresponse):
        """Helper method for tests"""
        self.create_date_data()
        resp = self.client.get(reverse('feedback-api'), getoptions)
        json_data = json.loads(resp.content)
        results = json_data['results']
        eq_(len(json_data['results']), len(expectedresponse))
        for result, expected in zip(results, expectedresponse):
            eq_(result['created'], expected)

    def test_date_start(self):
        """date_start returns responses from that day forward"""
        self._test_date(
            {'date_start': '2014-07-02'},
            ['2014-07-04T00:00:00', '2014-07-03T00:00:00',
             '2014-07-02T00:00:00'])

    def test_date_end(self):
        """date_end returns responses from before that day"""
        self._test_date(
            {'date_end': '2014-07-03'},
            ['2014-07-03T00:00:00', '2014-07-02T00:00:00',
                '2014-07-01T00:00:00'])

    def test_date_delta_with_date_end(self):
        """Test date_delta filtering when date_end exists"""
        self._test_date(
            {'date_delta': '1d', 'date_end': '2014-07-03'},
            ['2014-07-03T00:00:00', '2014-07-02T00:00:00'])

    def test_date_delta_with_date_start(self):
        """Test date_delta filtering when date_start exists"""
        self._test_date(
            {'date_delta': '1d', 'date_start': '2014-07-02'},
            ['2014-07-03T00:00:00', '2014-07-02T00:00:00'])

    def test_date_delta_with_date_end_and_date_start(self):
        """When all three date fields are specified ignore date_start"""
        self._test_date(
            {'date_delta': '1d', 'date_end': '2014-07-03',
            'date_start': '2014-07-02'},
            ['2014-07-03T00:00:00', '2014-07-02T00:00:00'])

    def test_date_delta_with_no_constraints(self):
        """Test date_delta filtering without date_end or date_start"""
        timeformatsuffix = 'T00:00:00'
        today = (str(date.today()) + timeformatsuffix)
        yesterday = (str(date.today() + timedelta(days=-1)) + timeformatsuffix)
        beforeyesterday = (str(date.today() + timedelta(days=-2)) +
                           timeformatsuffix)
        testdata = [
            (True, 'de', 'Firefox for Android', beforeyesterday),
            (True, 'en-US', 'Firefox', yesterday),
            (True, 'en-US', 'Firefox for Android', today)
        ]
        for happy, platform, product, date_start in testdata:
            ResponseFactory(
                happy=happy, platform=platform, product=product,
                created=date_start)
        self.refresh()
        self._test_date({'date_delta': '1d'}, [today, yesterday])

    def test_both_date_end_and_date_start_with_no_date_delta(self):
        self._test_date(
            {'date_start': '2014-07-02', 'date_end': '2014-07-03'},
            ['2014-07-03T00:00:00', '2014-07-02T00:00:00']
        )

    def test_public_fields(self):
        """The results should only contain publicly-visible fields"""
        # Note: This test might fail when we add new fields to
        # ES. What happens is that if a field doesn't have data when
        # the document is indexed, then there won't be a key/val in
        # the json results. Easy way to fix that is to make sure it
        # has a value when creating the response.
        ResponseFactory(api=True)
        self.refresh()

        resp = self.client.get(reverse('feedback-api'))
        json_data = json.loads(resp.content)
        eq_(json_data['count'], 1)
        eq_(sorted(json_data['results'][0].keys()),
            sorted(models.ResponseMappingType.public_fields()))


class PostFeedbackAPITest(TestCase):
    def setUp(self):
        super(PostFeedbackAPITest, self).setUp()
        # Make sure the unit tests aren't papering over CSRF issues.
        self.client = Client(enforce_csrf_checks=True)

    def test_minimal(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS'
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.happy, True)
        eq_(feedback.description, data['description'])
        eq_(feedback.product, data['product'])

        # Fills in defaults
        eq_(feedback.url, u'')
        eq_(feedback.api, 1)
        eq_(feedback.user_agent, u'')

    def test_maximal(self):
        """Tests an API call with all possible data"""
        data = {
            'happy': True,
            'description': u'Great!',
            'category': u'ui',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
            'email': 'foo@example.com',
            'url': 'http://example.com/',
            'manufacturer': 'OmniCorp',
            'device': 'OmniCorp',
            'country': 'US',
            'user_agent': (
                'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0'
            ),
            'source': 'email',
            'campaign': 'email_test',
        }

        # This makes sure the test is up-to-date. If we add fields
        # to the serializer, then this will error out unless we've
        # also added them to this test.
        for field in models.PostResponseSerializer.base_fields.keys():
            assert field in data, '{0} not in data'.format(field)

        # Post the data and then make sure everything is in the
        # resulting Response. In most cases, the field names line up
        # between PostResponseSerializer and Response with the
        # exception of 'email' which is stored in a different table.
        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        feedback = models.Response.objects.latest(field_name='id')
        for field in models.PostResponseSerializer.base_fields.keys():
            if field == 'email':
                email = models.ResponseEmail.objects.latest(field_name='id')
                eq_(email.email, data['email'])
            else:
                eq_(getattr(feedback, field), data[field])

    def test_with_email(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
            'email': 'foo@example.com'
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.happy, True)
        eq_(feedback.description, data['description'])
        eq_(feedback.platform, data['platform'])
        eq_(feedback.product, data['product'])
        eq_(feedback.channel, data['channel'])
        eq_(feedback.version, data['version'])

        # Fills in defaults
        eq_(feedback.url, u'')
        eq_(feedback.user_agent, u'')
        eq_(feedback.api, 1)

        email = models.ResponseEmail.objects.latest(field_name='id')
        eq_(email.email, data['email'])

    def test_with_context(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
            'email': 'foo@example.com',
            'slopmenow': 'bar'
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        context = models.ResponseContext.objects.latest(field_name='id')
        eq_(context.data, u'{"slopmenow": "bar"}')

    def test_with_context_truncate_key(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
            'email': 'foo@example.com',
            'foo012345678901234567890': 'bar'
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        context = models.ResponseContext.objects.latest(field_name='id')
        eq_(context.data, u'{"foo01234567890123456": "bar"}')

    def test_with_context_truncate_value(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
            'email': 'foo@example.com',
            'foo': ('a' * 100) + 'b'
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        context = models.ResponseContext.objects.latest(field_name='id')
        eq_(context.data, u'{"foo": "' + ('a' * 100) + '"}')

    def test_with_context_20_pairs(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
            'email': 'foo@example.com',
        }

        for i in range(25):
            data['foo%02d' % i] = str(i)

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        context = models.ResponseContext.objects.latest(field_name='id')
        data = sorted(json.loads(context.data).items())
        eq_(len(data), 20)
        eq_(data[0], ('foo00', '0'))
        eq_(data[-1], ('foo19', '19'))

    def test_null_device_returns_400(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'device': None
        }

        r = self.client.post(reverse('feedback-api'),
                             json.dumps(data),
                             content_type='application/json')
        eq_(r.status_code, 400)
        assert 'device' in r.content

    def test_invalid_email_address_returns_400(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
            'email': 'foo@example'
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 400)
        assert 'email' in r.content

    def test_composed_prodchan(self):
        # Test with product and channel
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        feedback = models.Response.uncached.latest(field_name='id')
        eq_(feedback.prodchan, u'firefoxos.stable')

        # Test with a product, but no channel
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 201)

        feedback = models.Response.uncached.latest(field_name='id')
        eq_(feedback.prodchan, u'firefoxos.unknown')

    # TODO: django-rest-framework 2.3.6 has a bug where BooleanField
    # has a default value of False, so "required=True" has no
    # effect. We really want to require that, so we'll have to wait
    # for a bug fix or something.
    #
    # def test_missing_happy_returns_400(self):
    #     data = {
    #         'description': u'Great!',
    #         'version': u'1.1',
    #         'platform': u'Firefox OS',
    #         'locale': 'en-US',
    #     }
    #
    #     r = self.client.post(reverse('feedback-api'), data)
    #     eq_(r.status_code, 400)
    #     assert 'happy' in r.content

    def test_missing_description_returns_400(self):
        data = {
            'happy': True,
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 400)
        assert 'description' in r.content

    def test_missing_product_returns_400(self):
        data = {
            'happy': True,
            'channel': u'stable',
            'version': u'1.1',
            'description': u'Great!',
            'platform': u'Firefox OS',
            'locale': 'en-US',
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 400)
        assert 'product' in r.content

    def test_invalid_product_returns_400(self):
        data = {
            'happy': True,
            'channel': u'stable',
            'version': u'1.1',
            'description': u'Great!',
            'product': u'Nurse Kitty',
            'platform': u'Firefox OS',
            'locale': 'en-US',
        }

        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 400)
        assert 'product' in r.content


class PostFeedbackAPIThrottleTest(TestCase):
    def test_throttle(self):
        # This test is a little goofy. Essentially we figure out what
        # the throttle trigger is, post that many times, then post
        # once more to see if it gets throttled. So if the trigger is
        # 100, then we post 101 times which seems kind of excessive
        # in a test.

        # Get the trigger so that we can post that many times + 1
        # to test throttling
        trigger = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['anon']
        trigger = int(trigger.split('/')[0])

        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
        }

        # Now hit the api a fajillion times making sure things got
        # created
        for i in range(trigger):
            r = self.client.post(reverse('feedback-api'), data)
            eq_(r.status_code, 201)

        # This one should trip the throttle trigger
        r = self.client.post(reverse('feedback-api'), data)
        eq_(r.status_code, 429)
