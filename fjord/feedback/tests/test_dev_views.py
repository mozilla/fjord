"""
Putting these in a separate file for now so they don't get mixed in with
the "regular stuff".

At some point p in the near future, the product picker version of the
code will become the "regular stuff". Then we'll move everything
around again.

FIXME: Merge these into test_views.py when the picker version lands.

"""
from django.core.cache import cache

from nose.tools import eq_

from fjord.base.tests import TestCase, LocalizingClient, reverse, with_waffle
from fjord.feedback import models
from fjord.feedback.tests import ProductFactory


@with_waffle('feedbackdev', True)
class TestPicker(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        # FIXME: We can nix this when we stop doing data migrations in
        # test setup.
        models.Product.objects.all().delete()

    def test_picker_no_products(self):
        resp = self.client.get(reverse('feedback'))

        eq_(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'feedback/picker.html')
        assert 'No products available.' in resp.content

    def test_picker_with_products(self):
        ProductFactory(display_name=u'ProductFoo', slug=u'productfoo')
        ProductFactory(display_name=u'ProductBar', slug=u'productbar')

        cache.clear()

        resp = self.client.get(reverse('feedback'))

        eq_(resp.status_code, 200)

        self.assertContains(resp, 'ProductFoo')
        self.assertContains(resp, 'productfoo')
        self.assertContains(resp, 'ProductBar')
        self.assertContains(resp, 'productbar')

    def test_picker_with_disabled_products(self):
        ProductFactory(display_name=u'ProductFoo', slug=u'productfoo',
                       enabled=True)
        ProductFactory(display_name=u'ProductBar', slug=u'productbar',
                       enabled=False)

        cache.clear()

        resp = self.client.get(reverse('feedback'))

        eq_(resp.status_code, 200)

        # This is on the picker
        self.assertContains(resp, 'ProductFoo')
        self.assertContains(resp, 'productfoo')

        # This is not on the picker
        self.assertNotContains(resp, 'ProductBar')
        self.assertNotContains(resp, 'productbar')

    def test_picker_with_not_on_picker_products(self):
        ProductFactory(display_name=u'ProductFoo', slug=u'productfoo',
                       on_picker=True)
        ProductFactory(display_name=u'ProductBar', slug=u'productbar',
                       on_picker=False)

        cache.clear()

        resp = self.client.get(reverse('feedback'))

        eq_(resp.status_code, 200)

        # This is on the picker
        self.assertContains(resp, 'ProductFoo')
        self.assertContains(resp, 'productfoo')

        # This is not on the picker
        self.assertNotContains(resp, 'ProductBar')
        self.assertNotContains(resp, 'productbar')


@with_waffle('feedbackdev', True)
class TestFeedbackDev(TestCase):
    client_class = LocalizingClient

    def test_generic_dev_view(self):
        url = reverse('feedback', args=('firefox',))
        resp = self.client.get(url)

        # Make sure it uses the feedback template. This includes the
        # feedback/generic_feedback_form_dev.html template, but we
        # can't easily test for that ...
        self.assertTemplateUsed(resp, 'feedback/generic_feedback.html')

        # unless we check for a magic string.
        assert '[DEV]' in resp.content

        # FIXME: Find a better way to verify dev version vs. non-dev
        # version.


@with_waffle('feedbackdev', False)
class TestFeedbackNotDev(TestCase):
    client_class = LocalizingClient

    def test_generic_dev_view(self):
        url = reverse('feedback', args=('firefox',))
        resp = self.client.get(url)

        # Make sure it uses the feedback template.
        self.assertTemplateUsed(resp, 'feedback/generic_feedback.html')

        # Make sure the magic string is NOT in the content.
        assert '[DEV]' not in resp.content
