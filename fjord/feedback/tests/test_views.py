from django.test.client import Client, RequestFactory
from nose.tools import eq_
from mock import NonCallableMock

from fjord.base.browsers import parse_ua
from fjord.base.tests import TestCase, LocalizingClient, reverse
from fjord.feedback import models
from fjord.feedback.views import _get_prodchan


class TestFeedback(TestCase):
    client_class = LocalizingClient

    def test_valid_happy(self):
        """Submitting a valid happy form creates an item in the DB.

        Additionally, it should redirect to the Thanks page.
        """
        amount = models.Simple.objects.count()

        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks!',
            'url': u'http://mozilla.org/'
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(amount + 1, models.Simple.objects.count())

        feedback = models.Simple.objects.latest(field_name='id')
        eq_(u'Firefox rocks!', feedback.description)
        eq_(u'http://mozilla.org/', feedback.url)
        eq_(True, feedback.happy)

    def test_valid_sad(self):
        """Submitting a valid sad form creates an item in the DB.

        Additionally, it should redirect to the Thanks page.
        """
        amount = models.Simple.objects.count()

        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'happy': 0,
            'description': u"Firefox doesn't make me sandwiches. :("
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(amount + 1, models.Simple.objects.count())

        feedback = models.Simple.objects.latest(field_name='id')
        eq_(u"Firefox doesn't make me sandwiches. :(", feedback.description)
        eq_(u'', feedback.url)
        eq_(False, feedback.happy)

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

    def test_feedback_router(self):
        """Requesting a generic template should give a feedback form."""
        # TODO: This test might need to change when the router starts routing.
        url = reverse('feedback')
        r = self.client.get(url, HTTP_USER_AGENT='Firefox')
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'feedback/feedback.html')

    def test_email_collection(self):
        """If the user enters an email and checks the box, collect the email."""
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u"I like the colors.",
            'email': 'bob@example.com',
            'email_ok': 1,
        })
        eq_(models.SimpleEmail.objects.count(), 1)
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
        assert not models.SimpleEmail.objects.exists()
        eq_(r.status_code, 302)

    def test_email_missing(self):
        """If an email is not entered and the box is checked, don't error out."""
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u'Can you fix it?',
            'email_ok': 1,
        })
        assert not models.SimpleEmail.objects.exists()
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
        assert not models.SimpleEmail.objects.exists()
        # No redirect to thank you page, since there is a form error.
        eq_(r.status_code, 200)
        self.assertContains(r, 'Please enter a valid email')

        r = self.client.post(url, {
            'happy': 0,
            'description': u'There is something wrong here.\0',
            'email_ok': 0,
            'email': "huh what's this for?",
        })
        assert not models.SimpleEmail.objects.exists()
        # Bad email if the box is not checked is not an error.
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
