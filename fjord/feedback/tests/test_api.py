from django.conf import settings

from nose.tools import eq_

from fjord.base.tests import TestCase, reverse
from fjord.feedback import models
from fjord.feedback.tests import product


class TestFeedbackAPI(TestCase):
    def setUp(self):
        super(TestFeedbackAPI, self).setUp()
        product(display_name=u'Firefox', save=True)
        product(display_name=u'Firefox OS', save=True)
        product(display_name=u'Firefox for Android', save=True)
        product(display_name=u'Firefox Metro', save=True)

    def test_minimal(self):
        data = {
            'happy': True,
            'description': u'Great!',
            'product': u'Firefox OS'
        }

        r = self.client.post(reverse('api-post-feedback'), data)
        eq_(r.status_code, 201)

        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.happy, True)
        eq_(feedback.description, data['description'])
        eq_(feedback.product, data['product'])

        # Fills in defaults
        eq_(feedback.url, u'')
        eq_(feedback.user_agent, u'api')

    def test_maximal(self):
        """Tests an API call with all possible data"""
        data = {
            'happy': True,
            'description': u'Great!',
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
        }

        # This makes sure the test is up-to-date. If we add fields
        # to the serializer, then this will error out unless we've
        # also added them to this test.
        for field in models.ResponseSerializer.base_fields.keys():
            assert field in data, '{0} not in data'.format(field)

        # Post the data and then make sure everything is in the
        # resulting Response. In most cases, the field names line up
        # between ResponseSerializer and Response with the exception
        # of 'email' which is stored in a different table.
        r = self.client.post(reverse('api-post-feedback'), data)
        eq_(r.status_code, 201)

        feedback = models.Response.objects.latest(field_name='id')
        for field in models.ResponseSerializer.base_fields.keys():
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

        r = self.client.post(reverse('api-post-feedback'), data)
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
        eq_(feedback.user_agent, u'api')

        email = models.ResponseEmail.objects.latest(field_name='id')
        eq_(email.email, data['email'])

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

        r = self.client.post(reverse('api-post-feedback'), data)
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

        r = self.client.post(reverse('api-post-feedback'), data)
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

        r = self.client.post(reverse('api-post-feedback'), data)
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
    #     r = self.client.post(reverse('api-post-feedback'), data)
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

        r = self.client.post(reverse('api-post-feedback'), data)
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

        r = self.client.post(reverse('api-post-feedback'), data)
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

        r = self.client.post(reverse('api-post-feedback'), data)
        eq_(r.status_code, 400)
        assert 'product' in r.content

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
            r = self.client.post(reverse('api-post-feedback'), data)
            eq_(r.status_code, 201)

        # This one should trip the throttle trigger
        r = self.client.post(reverse('api-post-feedback'), data)
        eq_(r.status_code, 429)
