# -*- coding: utf-8 -*-
import json
import random
import time
from datetime import date, datetime, timedelta

from django.core.cache import get_cache
from django.test.client import Client

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
        assert json_data['count'] == 3
        assert len(json_data['results']) == 3

    def test_id(self):
        feedback = ResponseFactory()
        self.refresh()

        resp = self.client.get(reverse('feedback-api'), {'id': feedback.id})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 1
        assert len(json_data['results']) == 1
        assert json_data['results'][0]['id'] == feedback.id

    def test_multiple_ids(self):
        # Create some responses that we won't ask for
        for i in range(5):
            ResponseFactory()

        resps = []
        for i in range(5):
            resps.append(ResponseFactory())

        self.refresh()

        resp = self.client.get(
            reverse('feedback-api'),
            {'id': ','.join([str(int(f.id)) for f in resps])}
        )
        json_data = json.loads(resp.content)
        assert json_data['count'] == 5
        assert len(json_data['results']) == 5
        assert(
            sorted([item['id'] for item in json_data['results']]) ==
            sorted([feedback.id for feedback in resps])
        )

    def test_junk_ids(self):
        """Junk ids should just get ignored"""
        feedback = ResponseFactory()
        self.refresh()

        resp = self.client.get(
            reverse('feedback-api'),
            {'id': str(feedback.id) + ',foo'}
        )
        json_data = json.loads(resp.content)
        assert json_data['count'] == 1
        assert len(json_data['results']) == 1
        assert json_data['results'][0]['id'] == feedback.id

    def test_happy(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'), {'happy': '1'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 2
        assert len(json_data['results']) == 2

    def test_platforms(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'), {'platforms': 'Linux'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 1
        assert len(json_data['results']) == 1

        resp = self.client.get(reverse('feedback-api'),
                               {'platforms': 'Linux,Windows'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 2
        assert len(json_data['results']) == 2

    def test_products_and_versions(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'),
                               {'products': 'Firefox'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 2
        assert len(json_data['results']) == 2

        resp = self.client.get(reverse('feedback-api'),
                               {'products': 'Firefox,Firefox for Android'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 3
        assert len(json_data['results']) == 3

        # version without product gets ignored
        resp = self.client.get(reverse('feedback-api'),
                               {'versions': '30.0'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 3
        assert len(json_data['results']) == 3

        resp = self.client.get(reverse('feedback-api'),
                               {'products': 'Firefox',
                                'versions': '30.0'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 1
        assert len(json_data['results']) == 1

    def test_locales(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'), {'locales': 'en-US'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 2
        assert len(json_data['results']) == 2

        resp = self.client.get(reverse('feedback-api'),
                               {'locales': 'en-US,de'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 3
        assert len(json_data['results']) == 3

    def test_multi_filter(self):
        self.create_basic_data()

        # Locale and happy
        resp = self.client.get(reverse('feedback-api'), {
            'locales': 'de', 'happy': 1
        })
        json_data = json.loads(resp.content)
        assert json_data['count'] == 0
        assert len(json_data['results']) == 0

    def test_query(self):
        self.create_basic_data()

        resp = self.client.get(reverse('feedback-api'), {'q': 'desc'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 2
        assert len(json_data['results']) == 2

    def test_old_responses(self):
        # Make sure we can't see responses from > 180 days ago
        cutoff = datetime.today() - timedelta(days=180)
        ResponseFactory(description='Young enough--Party!',
                        created=cutoff + timedelta(days=1))
        ResponseFactory(description='Too old--Get off my lawn!',
                        created=cutoff - timedelta(days=1))
        self.refresh()

        resp = self.client.get(reverse('feedback-api'), {
            'date_start': (cutoff - timedelta(days=1)).strftime('%Y-%m-%d'),
            'date_end': (cutoff + timedelta(days=1)).strftime('%Y-%m-%d')
        })
        json_data = json.loads(resp.content)
        results = json_data['results']
        assert len(results) == 1

        assert 'Young enough--Party!' in resp.content
        assert 'Too old--Get off my lawn!' not in resp.content

    def test_public_fields(self):
        """The results should only contain publicly-visible fields"""
        # Note: This test might fail when we add new fields to
        # ES. What happens is that if a field doesn't have data when
        # the document is indexed, then there won't be a key/val in
        # the json results. Easy way to fix that is to make sure it
        # has a value when creating the response.
        ResponseFactory(description=u'best browser ever', api=True)
        self.refresh()

        resp = self.client.get(reverse('feedback-api'))
        json_data = json.loads(resp.content)
        assert json_data['count'] == 1
        assert(
            sorted(json_data['results'][0].keys()) ==
            sorted(models.ResponseDocType.public_fields()))

    def test_max(self):
        for i in range(10):
            ResponseFactory(description=u'best browser ever %d' % i)
        self.refresh()

        resp = self.client.get(reverse('feedback-api'))
        json_data = json.loads(resp.content)
        assert json_data['count'] == 10

        resp = self.client.get(reverse('feedback-api'), {'max': '5'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 5

        # FIXME: For now, nonsense values get ignored.
        resp = self.client.get(reverse('feedback-api'), {'max': 'foo'})
        json_data = json.loads(resp.content)
        assert json_data['count'] == 10


class PublicFeedbackAPIDateTest(ElasticTestCase):
    # Get the YYYY-MM part of the date for last month. We use last
    # month since arbitrarily appending the day will always create
    # dates in the past.
    last_month = str(date.today() - timedelta(days=31))[:7]

    def create_data(self, days):
        """Create response data for specified days

        This creates the specified responses and also refreshes the
        Elasticsearch index.

        :arg days: List of day-of-month strings. For example
            ``['01', '02', '03']``

        """
        for day in days:
            ResponseFactory(created=self.last_month + '-' + day)
        self.refresh()

    def _test_date(self, params, expected):
        """Helper method for tests"""
        resp = self.client.get(reverse('feedback-api'), params)
        json_data = json.loads(resp.content)
        results = json_data['results']
        assert len(json_data['results']) == len(expected)
        for result, expected in zip(results, expected):
            assert result['created'] == expected + 'T00:00:00'

    def test_date_start(self):
        """date_start returns responses from that day forward"""
        self.create_data(['01', '02', '03', '04'])

        self._test_date(
            params={'date_start': self.last_month + '-02'},
            expected=[
                self.last_month + '-04',
                self.last_month + '-03',
                self.last_month + '-02'
            ])

    def test_date_end(self):
        """date_end returns responses from before that day"""
        self.create_data(['01', '02', '03', '04'])

        self._test_date(
            params={'date_end': self.last_month + '-03'},
            expected=[
                self.last_month + '-03',
                self.last_month + '-02',
                self.last_month + '-01'
            ])

    def test_date_delta_with_date_end(self):
        """Test date_delta filtering when date_end exists"""
        self.create_data(['01', '02', '03', '04'])

        self._test_date(
            params={'date_delta': '1d', 'date_end': self.last_month + '-03'},
            expected=[
                self.last_month + '-03',
                self.last_month + '-02'
            ])

    def test_date_delta_with_date_start(self):
        """Test date_delta filtering when date_start exists"""
        self.create_data(['01', '02', '03', '04'])

        self._test_date(
            params={'date_delta': '1d', 'date_start': self.last_month + '-02'},
            expected=[
                self.last_month + '-03',
                self.last_month + '-02'
            ])

    def test_date_delta_with_date_end_and_date_start(self):
        """When all three date fields are specified ignore date_start"""
        self.create_data(['01', '02', '03', '04'])

        self._test_date(
            params={
                'date_delta': '1d',
                'date_end': self.last_month + '-03',
                'date_start': self.last_month + '-02'
            },
            expected=[
                self.last_month + '-03',
                self.last_month + '-02'
            ])

    def test_date_delta_with_no_constraints(self):
        """Test date_delta filtering without date_end or date_start"""
        today = str(date.today())
        yesterday = str(date.today() + timedelta(days=-1))
        beforeyesterday = str(date.today() + timedelta(days=-2))

        for d in [beforeyesterday, yesterday, today]:
            ResponseFactory(created=d)
        self.refresh()

        self._test_date(
            params={'date_delta': '1d'},
            expected=[
                today,
                yesterday
            ])

    def test_both_date_end_and_date_start_with_no_date_delta(self):
        self.create_data(['01', '02', '03', '04'])

        self._test_date(
            params={
                'date_start': self.last_month + '-02',
                'date_end': self.last_month + '-03'
            },
            expected=[
                self.last_month + '-03',
                self.last_month + '-02'
            ])


class FeedbackHistogramAPITest(ElasticTestCase):
    def generate_response(self, created, description=u'So awesome!'):
        ResponseFactory(
            created=datetime(created.year, created.month, created.day,
                             random.randint(0, 23), 0),
            description=description
        )

    def to_date_string(self, value):
        """Takes a milliseconds since epoch int and converts to string"""
        d = time.gmtime(value / 1000)
        return time.strftime('%Y-%m-%d %H:%M:%S', d)

    def test_basic(self):
        """Show last 7 days of counts"""
        today = date.today()
        for i in range(8):
            self.generate_response(today - timedelta(days=i))
            self.generate_response(today - timedelta(days=i))
        self.refresh()

        resp = self.client.get(reverse('feedback-histogram-api'))
        assert resp.status_code == 200
        json_data = json.loads(resp.content)

        # Default is the last 7 days.
        assert len(json_data['results']) == 7

        # Last item in the list should be yesterday.
        assert(
            self.to_date_string(json_data['results'][-1][0]) ==
            (today - timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
        )
        # Count is 2.
        assert json_data['results'][-1][1] == 2

        # First item is 7 days ago.
        assert(
            self.to_date_string(json_data['results'][0][0]) ==
            (today - timedelta(days=7)).strftime('%Y-%m-%d 00:00:00')
        )
        # Count is 2.
        assert json_data['results'][0][1] == 2

    def test_q(self):
        """Test q argument"""
        dt = date.today() - timedelta(days=1)
        self.generate_response(created=dt, description='pocket pocket')
        self.generate_response(created=dt, description='video video')
        self.refresh()

        resp = self.client.get(reverse('feedback-histogram-api'), {
            'q': 'pocket'
        })
        assert resp.status_code == 200
        json_data = json.loads(resp.content)

        # Default range ends yesterday. Only one response with
        # "pocket" in it yesterday, so this is 1.
        assert json_data['results'][-1][1] == 1

    # FIXME: Test date_start, date_end and date_delta
    # FIXME: Test products, versions
    # FIXME: Test locales
    # FIXME: Test happy/sad
    # FIXME: Test platforms
    # FIXME: Test interval


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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.happy == True
        assert feedback.description == data['description']
        assert feedback.product == data['product']

        # Fills in defaults
        assert feedback.url == u''
        assert feedback.api == 1
        assert feedback.user_agent == u''

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
        prs = models.PostResponseSerializer()
        for field in prs.fields.keys():
            assert field in data, '{0} not in data'.format(field)

        # Post the data and then make sure everything is in the
        # resulting Response. In most cases, the field names line up
        # between PostResponseSerializer and Response with the
        # exception of 'email' which is stored in a different table.
        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        feedback = models.Response.objects.latest(field_name='id')
        for field in prs.fields.keys():
            if field == 'email':
                email = models.ResponseEmail.objects.latest(field_name='id')
                assert email.email == data['email']
            else:
                assert getattr(feedback, field) == data[field]

    def test_missing_happy_defaults_to_sad(self):
        # We want to require "happy" to be in the values, but for
        # various reasons we can't. Instead, if it's not provided, we
        # want to make sure it defaults to sad.
        data = {
            'description': u'Great!',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'product': u'Firefox OS',
            'locale': 'en-US',
        }

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.happy == False

    def test_whitespace_description_is_invalid(self):
        data = {
            'happy': True,
            'description': u' ',
            'product': u'Firefox OS'
        }

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 400

    def test_blank_category_is_fine_we_suppose(self):
        data = {
            'happy': True,
            'description': u'happy',
            'product': u'Loop',
            'category': u''
        }

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

    def test_invalid_unicode_url(self):
        """Tests an API call with invalid unicode URL"""
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
            'url': 'தமிழகம்',
            'manufacturer': 'OmniCorp',
            'device': 'OmniCorp',
            'country': 'US',
            'user_agent': (
                'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0'
            ),
            'source': 'email',
            'campaign': 'email_test',
        }
        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))

        assert r.status_code == 400
        content = json.loads(r.content)
        assert u'url' in content
        assert content['url'][0].endswith(u'is not a valid url')

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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.happy == True
        assert feedback.description == data['description']
        assert feedback.platform == data['platform']
        assert feedback.product == data['product']
        assert feedback.channel == data['channel']
        assert feedback.version == data['version']

        # Fills in defaults
        assert feedback.url == u''
        assert feedback.user_agent == u''
        assert feedback.api == 1

        email = models.ResponseEmail.objects.latest(field_name='id')
        assert email.email == data['email']

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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        context = models.ResponseContext.objects.latest(field_name='id')
        assert context.data == {'slopmenow': 'bar'}

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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        context = models.ResponseContext.objects.latest(field_name='id')
        assert context.data, {'foo01234567890123456': 'bar'}

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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        context = models.ResponseContext.objects.latest(field_name='id')
        assert context.data == {'foo': ('a' * 100)}

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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        context = models.ResponseContext.objects.latest(field_name='id')
        data = sorted(context.data.items())
        assert len(data) == 20
        assert data[0] == ('foo00', '0')
        assert data[-1] == ('foo19', '19')

    def test_null_device_returns_400(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'device': None
        }

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 400
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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 400
        assert 'email' in r.content

    def test_missing_description_returns_400(self):
        data = {
            'happy': True,
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
        }

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 400
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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 400
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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 400
        assert 'product' in r.content

    def test_url_max_length(self):
        url_base = 'http://example.com/'

        # Up to 199 characters is fine.
        data = {
            'happy': True,
            'channel': u'stable',
            'version': u'1.1',
            'description': u'Great! 199',
            'product': u'Firefox OS',
            'platform': u'Firefox OS',
            'url': url_base + ('a' * (199 - len(url_base))) + 'b',
            'locale': 'en-US',
        }

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        # 200th character is not fine.
        data = {
            'happy': True,
            'channel': u'stable',
            'version': u'1.1',
            'description': u'Great! 200',
            'product': u'Firefox OS',
            'platform': u'Firefox OS',
            'url': url_base + ('a' * (200 - len(url_base))) + 'b',
            'locale': 'en-US',
        }

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 400

    def test_valid_urls(self):
        test_data = [
            'example.com',
            'example.com:80',
            'example.com:80/foo',
            'http://example.com',
            'http://example.com/foo',
            'http://example.com:80',
            'http://example.com:80/foo',
            'https://example.com',
            'https://example.com/foo',
            'https://example.com:80',
            'https://example.com:80/foo',
            'ftp://example.com',
            'about:mozilla',
            'chrome://foo'
        ]
        for url in test_data:
            data = {
                'happy': True,
                'channel': u'stable',
                'version': u'1.1',
                'description': u'Great!',
                'product': u'Firefox OS',
                'platform': u'Firefox OS',
                'url': url,
                'locale': 'en-US',
            }

            r = self.client.post(
                reverse('feedback-api'),
                content_type='application/json',
                data=json.dumps(data))
            assert (r.status_code == 201,
                ('%s != 201 (%s)' % (r.status_code, url))
                )

            get_cache('default').clear()

    def test_user_agent_inferred_bits(self):
        """Tests that we infer the right bits from the user-agent"""
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

        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.browser == u'Firefox OS'
        assert feedback.browser_version == u'1.0'
        assert feedback.browser_platform == u'Firefox OS'


class PostFeedbackAPIThrottleTest(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()

        get_cache('default').clear()

    def test_throttle(self):
        # We allow 50 posts per hour.
        throttle_trigger = 50

        # Descriptions have to be unique otherwise we hit the
        # double-submit throttling. So we do this fancy thing here.
        def data_generator():
            while True:
                yield {
                    'happy': True,
                    'description': u'Great! ' + str(time.time()),
                    'product': u'Firefox OS',
                    'channel': u'stable',
                    'version': u'1.1',
                    'platform': u'Firefox OS',
                    'locale': 'en-US',
                }

        data = data_generator()

        # Now hit the api a fajillion times making sure things got
        # created
        for i in range(throttle_trigger):
            # django-ratelimit fails the throttling if we hit the url
            # a fajillion times in rapid succession. For now, we add
            # a sleep which means this test takes 5 seconds now.
            # FIXME: Look into this more for a better solution.
            time.sleep(0.05)
            r = self.client.post(
                reverse('feedback-api'),
                content_type='application/json',
                data=json.dumps(data.next()))
            assert r.status_code == 201

        # This one should trip the throttle trigger
        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data.next()))
        assert r.status_code == 429

    def test_double_submit_throttle(self):
        # We disallow two submits in a row of the same description
        # from the same ip address.
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS',
            'channel': u'stable',
            'version': u'1.1',
            'platform': u'Firefox OS',
            'locale': 'en-US',
        }

        # First time is fine
        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 201

        # Second time and back off!
        r = self.client.post(
            reverse('feedback-api'),
            content_type='application/json',
            data=json.dumps(data))
        assert r.status_code == 429
