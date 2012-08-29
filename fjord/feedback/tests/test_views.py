from fjord.base.tests import TestCase, LocalizingUAClient, reverse
from nose.tools import eq_

from fjord.feedback import models


class TestFeedback(TestCase):
    client_class = LocalizingUAClient

    def test_valid_happy(self):
        """Submitting a valid happy form creates an item in the DB.
        Additionally, we should end up at the Thanks page.
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
        """Submitting a valid happy form creates an item in the DB.
        Additionally, we should end up at the Thanks page.
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
        """Submitting a bad form should send us back to the same page and
        return a 400.
        """
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/'
            # No happy/sad
            # No description
        })

        eq_(400, r.status_code)
        self.assertTemplateUsed(r, 'feedback/feedback.html')

    def test_feedback_router(self):
        """Requesting a generic template should give a feedback form."""
        #TODO: This test might need to change when the router starts routing.
        url = reverse('feedback')
        r = self.client.get(url)
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'feedback/feedback.html')
