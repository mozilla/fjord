from django.test.client import RequestFactory
from nose.tools import eq_
from mock import NonCallableMock

from fjord.base.browsers import parse_ua
from fjord.base.tests import TestCase, LocalizingClient, reverse
from fjord.feedback import models
from fjord.feedback.views import _get_prodchan


class TestRedirectFeedback(TestCase):
    client_class = LocalizingClient

    def test_happy_redirect(self):
        r = self.client.get(reverse('happy-redirect'))
        self.assertRedirects(r, reverse('feedback') + '#happy')

    def test_sad_redirect(self):
        r = self.client.get(reverse('sad-redirect'))
        self.assertRedirects(r, reverse('feedback') + '#sad')


class TestFeedback(TestCase):
    client_class = LocalizingClient

    def test_valid_happy(self):
        """Submitting a valid happy form creates an item in the DB.

        Additionally, it should redirect to the Thanks page.
        """
        amount = models.Response.objects.count()

        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks!',
            'url': u'http://mozilla.org/'
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())

        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'Firefox rocks!', feedback.description)
        eq_(u'http://mozilla.org/', feedback.url)
        eq_(True, feedback.happy)

        # This comes from the client.post url.
        eq_(u'en-US', feedback.locale)
        # Note: This comes from the user agent from the LocalizingClient
        eq_(u'Firefox', feedback.product)
        eq_(u'stable', feedback.channel)
        eq_(u'14.0.1', feedback.version)

    def test_valid_sad(self):
        """Submitting a valid sad form creates an item in the DB.

        Additionally, it should redirect to the Thanks page.
        """
        amount = models.Response.objects.count()

        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'happy': 0,
            'description': u"Firefox doesn't make me sandwiches. :("
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())

        feedback = models.Response.objects.latest(field_name='id')
        eq_(u"Firefox doesn't make me sandwiches. :(", feedback.description)
        eq_(u'', feedback.url)
        eq_(False, feedback.happy)

        # This comes from the client.post url.
        eq_(u'en-US', feedback.locale)
        # Note: This comes from the user agent from the LocalizingClient
        eq_(u'Firefox', feedback.product)
        eq_(u'stable', feedback.channel)
        eq_(u'14.0.1', feedback.version)

    def test_invalid_form(self):
        """Submitting a bad form should return an error and not change pages."""
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/'
            # No happy/sad
            # No description
        })

        self.assertContains(r, 'This field is required')
        self.assertTemplateUsed(r, 'feedback/feedback.html')

        # Test happy sans description
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0
            # No description
        })

        self.assertContains(r, 'This field is required')

        # Test sad sans description
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 1
            # No description
        })

        self.assertContains(r, 'This field is required')

    def test_whitespace_description(self):
        """Descriptions should have more than just whitespace"""
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0,
            'description': u'      '
        })

        self.assertContains(r, 'This field is required')
        self.assertTemplateUsed(r, 'feedback/feedback.html')

    def test_unicode_in_description(self):
        """Description should accept unicode data"""
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0,
            'description': u'\u2713 this works'
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 1)

    def test_unicode_in_url(self):
        """URL should accept unicode data"""
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'url': u'http://mozilla.org/\u2713',
            'happy': 0,
            'description': u'foo'
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 1)

    def test_feedback_router(self):
        """Requesting a generic template should give a feedback form."""
        # TODO: This test might need to change when the router starts routing.
        url = reverse('feedback')
        ua = ('Mozilla/5.0 (X11; Linux x86_64; rv:21.0) Gecko/20130212 '
              'Firefox/21.0')

        r = self.client.get(url, HTTP_USER_AGENT=ua)
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'feedback/feedback.html')

    def test_reject_non_firefox(self):
        """Using non-Firefox browser lands you on download-firefox page."""
        # TODO: This test might need to change when the router starts routing.
        url = reverse('feedback')

        for ua in (
            ('Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; '
             'Trident/5.0)'),
            ('Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 '
             '(KHTML, like Gecko) Chrome/24.0.1312.68 Safari/537.17'),
            ('Mozilla/5.0 (Linux; U; Android 4.0.2; en-us; Galaxy Nexus '
             'Build/ICL53F) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 '
             'Mobile Safari/534.30'),
            ('Mozilla/5.0 (Linux; U; Android 4.0.4; en-us; Xoom Build/IMM76) '
             'AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 '
             'Safari/534.30'),
            ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.22 (KHTML, like '
             'Gecko) Chrome/25.0.1364.97 Safari/537.22')):

            r = self.client.get(url, HTTP_USER_AGENT=ua)
            self.assertRedirects(r, reverse('download-firefox'))

    def test_email_collection(self):
        """If the user enters an email and checks the box, collect the email."""
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u"I like the colors.",
            'email': 'bob@example.com',
            'email_ok': 1,
        })
        eq_(models.ResponseEmail.objects.count(), 1)
        eq_(r.status_code, 302)

    def test_email_privacy(self):
        """If an email is entered, but the box is not checked, don't collect."""
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u"I like the colors.",
            'email': 'bob@example.com',
            'email_ok': 0,
        })
        assert not models.ResponseEmail.objects.exists()
        eq_(r.status_code, 302)

    def test_email_missing(self):
        """If an email is not entered and the box is checked, don't error out."""
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u'Can you fix it?',
            'email_ok': 1,
        })
        assert not models.ResponseEmail.objects.exists()
        # No redirect to thank you page, since there is a form error.
        eq_(r.status_code, 200)
        self.assertContains(r, 'Please enter a valid email')

    def test_email_invalid(self):
        """If an email is not entered and the box is checked, don't error out."""
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u'There is something wrong here.\0',
            'email_ok': 1,
            'email': '/dev/sda1\0',
        })
        assert not models.ResponseEmail.objects.exists()
        # No redirect to thank you page, since there is a form error.
        eq_(r.status_code, 200)
        self.assertContains(r, 'Please enter a valid email')

        r = self.client.post(url, {
            'happy': 0,
            'description': u'There is something wrong here.\0',
            'email_ok': 0,
            'email': "huh what's this for?",
        })
        assert not models.ResponseEmail.objects.exists()
        # Bad email if the box is not checked is not an error.
        eq_(r.status_code, 302)

    def test_deprecated_firefox_for_android_feedback_works(self):
        """Verify firefox for android can post feedback"""
        data = {
            '_type': 1,
            'description': u'Firefox rocks!',
            'add_url': 1,
            'url': u'http://mozilla.org/',
            'device': 'Stone tablet',
            'manufacturer': 'Rosetta'
            }

        ua = 'Mozilla/5.0 (Android; Tablet; rv:24.0) Gecko/24.0 Firefox/24.0'

        r = self.client.post(reverse('feedback'), data, HTTP_USER_AGENT=ua)
        eq_(r.status_code, 302)
        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.happy, True)
        eq_(feedback.url, data['url'])
        eq_(feedback.description, data['description'])
        eq_(feedback.device, data['device'])
        eq_(feedback.manufacturer, data['manufacturer'])

        # This comes from the client.post url.
        eq_(u'en-US', feedback.locale)
        # Note: This comes from the user agent from the LocalizingClient
        eq_(u'Firefox for Android', feedback.product)
        eq_(u'stable', feedback.channel)
        eq_(u'24.0.0', feedback.version)

    def test_deprecated_firefox_for_android_sad_is_sad(self):
        data = {
            '_type': 2,
            'description': u'This is how to make it better...',
            'add_url': 1,
            'url': u'http://mozilla.org/',
            'device': 'Stone tablet',
            'manufacturer': 'Rosetta'
            }

        ua = 'Mozilla/5.0 (Android; Tablet; rv:24.0) Gecko/24.0 Firefox/24.0'

        r = self.client.post(reverse('feedback'), data, HTTP_USER_AGENT=ua)
        eq_(r.status_code, 302)
        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.happy, False)
        eq_(feedback.url, data['url'])
        eq_(feedback.description, data['description'])

        # This comes from the client.post url.
        eq_(u'en-US', feedback.locale)
        # Note: This comes from the user agent from the LocalizingClient
        eq_(u'Firefox for Android', feedback.product)
        eq_(u'stable', feedback.channel)
        eq_(u'24.0.0', feedback.version)

    def test_deprecated_firefox_for_android_ideas_are_sad(self):
        """We treat "sad" and "ideas" as sad feedback now."""
        data = {
            '_type': 3,
            'description': u'This is how to make it better...',
            'add_url': 1,
            'url': u'http://mozilla.org/',
            'device': 'Stone tablet',
            'manufacturer': 'Rosetta'
            }

        ua = 'Mozilla/5.0 (Android; Tablet; rv:24.0) Gecko/24.0 Firefox/24.0'

        r = self.client.post(reverse('feedback'), data, HTTP_USER_AGENT=ua)
        eq_(r.status_code, 302)
        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.happy, False)
        eq_(feedback.url, data['url'])
        eq_(feedback.description, data['description'])

        # This comes from the client.post url.
        eq_(u'en-US', feedback.locale)
        # Note: This comes from the user agent from the LocalizingClient
        eq_(u'Firefox for Android', feedback.product)
        eq_(u'stable', feedback.channel)
        eq_(u'24.0.0', feedback.version)

    def test_deprecated_firefox_for_android_minimal(self):
        """Test the minimal post data from FfA works."""
        data = {
            '_type': 1,
            'description': u'This is how to make it better...',
            'device': 'Stone tablet',
            'manufacturer': 'Rosetta'
            }

        ua = 'Mozilla/5.0 (Android; Tablet; rv:24.0) Gecko/24.0 Firefox/24.0'

        r = self.client.post(reverse('feedback'), data, HTTP_USER_AGENT=ua)
        eq_(r.status_code, 302)
        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.happy, True)
        eq_(feedback.url, u'')
        eq_(feedback.description, data['description'])

        # This comes from the client.post url.
        eq_(u'en-US', feedback.locale)
        # Note: This comes from the user agent from the LocalizingClient
        eq_(u'Firefox for Android', feedback.product)
        eq_(u'stable', feedback.channel)
        eq_(u'24.0.0', feedback.version)

    def test_deprecated_firefox_for_android_phony_ua(self):
        """Test that phony user agents works. bug 855671."""
        data = {
            '_type': 1,
            'description': u'This is how to make it better...',
            'device': 'Stone tablet',
            'manufacturer': 'Rosetta'
            }

        ua = ('Mozilla/5.0 (Linux; U; Android 4.0.4; en-us; Xoom '
              'Build/IMM76) AppleWebKit/534.30 (KHTML, like Gecko) '
              'Version/4.0 Safari/534.30')

        r = self.client.post(reverse('feedback'), data,
                             HTTP_USER_AGENT=ua)
        eq_(r.status_code, 302)
        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.browser, 'Unknown')
        eq_(feedback.browser_version, 'Unknown')
        eq_(feedback.platform, 'Unknown')

        # This comes from the client.post url.
        eq_(u'en-US', feedback.locale)
        # Note: This comes from the user agent from the LocalizingClient
        eq_(u'Unknown', feedback.product)
        eq_(u'Unknown', feedback.channel)
        eq_(u'Unknown', feedback.version)


class TestCSRF(TestCase):
    def setUp(self):
        super(TestCSRF, self).setUp()
        self.factory = RequestFactory()
        self.client = LocalizingClient(enforce_csrf_checks=True)

    def test_no_csrf_regular_form_fails(self):
        """No csrf token in post data from anonymous user yields 403."""
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks!',
            'url': u'http://mozilla.org/'
        })

        eq_(r.status_code, 403)

    def test_firefox_for_android(self):
        """No csrf token for a FfA post works fine."""
        url = reverse('feedback')
        r = self.client.post(url, {
            '_type': 1,
            'description': u'Firefox rocks!',
            'add_url': 1,
            'url': u'http://mozilla.org/'
        })
        eq_(r.status_code, 302)


class TestRouting(TestCase):

    uas = {
        'android': 'Mozilla/5.0 (Android; Mobile; rv:18.0) Gecko/18.0 '
                   'Firefox/18.0',
        'linux': 'Mozilla/5.0 (X11; Linux x86_64; rv:21.0) Gecko/20130212 '
                 'Firefox/21.0',
        'osx': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:20.0) '
               'Gecko/20130208 Firefox/20.0',
    }

    def setUp(self):
        super(TestRouting, self).setUp()
        self.factory = RequestFactory()

    def sub_routing(self, ua, mobile):
        url = reverse('feedback')
        extra = {
            'HTTP_USER_AGENT': ua,
        }
        r = self.client.get(url, **extra)
        if mobile:
            self.assertTemplateUsed(r, 'feedback/mobile/feedback.html')
        else:
            self.assertTemplateUsed(r, 'feedback/feedback.html')

    def test_routing(self):
        self.sub_routing(self.uas['android'], True)
        self.sub_routing(self.uas['osx'], False)
        self.sub_routing(self.uas['linux'], False)

    def sub_prodchan(self, ua, prodchan):
        # _get_prodchan checks request.BROWSER to decide what to do, so
        # give it a mocked object that has that.
        fake_req = NonCallableMock(BROWSER=parse_ua(ua))
        eq_(prodchan, _get_prodchan(fake_req))

    def test_prodchan(self):
        self.sub_prodchan(self.uas['android'], 'firefox.android.stable')
        self.sub_prodchan(self.uas['osx'], 'firefox.desktop.stable')
        self.sub_prodchan(self.uas['linux'], 'firefox.desktop.stable')
