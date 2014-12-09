from django.core.cache import cache
from django.test.client import RequestFactory
from django.test.utils import override_settings

from nose.tools import eq_

from fjord.base.tests import TestCase, LocalizingClient, reverse
from fjord.feedback import models
from fjord.feedback.tests import ProductFactory


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

        url = reverse('feedback', args=(u'firefox',))
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
        eq_(u'14.0.1', feedback.version)

        # Make sure it doesn't create an email record
        eq_(models.ResponseEmail.objects.count(), 0)

        # Make sure it doesn't create a context record
        eq_(models.ResponseContext.objects.count(), 0)

    def test_valid_sad(self):
        """Submitting a valid sad form creates an item in the DB.

        Additionally, it should redirect to the Thanks page.
        """
        amount = models.Response.objects.count()

        url = reverse('feedback', args=(u'firefox',))
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
        eq_(u'14.0.1', feedback.version)

    def test_firefox_os_view(self):
        """Firefox OS returns correct view"""
        # Firefox OS is the user agent
        url = reverse('feedback')
        ua = 'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0'
        r = self.client.get(url, HTTP_USER_AGENT=ua)
        self.assertTemplateUsed(r, 'feedback/fxos_feedback.html')

        # Specifying fxos as the product in the url
        url = reverse('feedback', args=(u'fxos',))
        r = self.client.get(url)
        self.assertTemplateUsed(r, 'feedback/fxos_feedback.html')

    def test_firefox_os_view_works_for_all_browsers(self):
        """Firefox OS feedback form should work for all browsers"""
        # Firefox OS is the user agent
        url = reverse('feedback', args=(u'fxos',))
        ua = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1944.0 '
            'Safari/537.36'
        )
        r = self.client.get(url, HTTP_USER_AGENT=ua)
        self.assertTemplateUsed(r, 'feedback/fxos_feedback.html')

    @override_settings(DEV_LANGUAGES=('en-US', 'es'))
    def test_urls_locale(self):
        """Test setting locale from the locale part of the url"""
        try:
            count = models.Response.uncached.count()

            # Hard-coded url so we're guaranteed to get /es/.
            url = '/es/feedback/firefox'
            resp = self.client.post(url, {
                'happy': 1,
                'description': u'Firefox rocks for es!',
                'url': u'http://mozilla.org/'
            })

            self.assertRedirects(resp, reverse('thanks'))
            eq_(count + 1, models.Response.uncached.count())
            feedback = models.Response.objects.latest(field_name='id')
            eq_(u'es', feedback.locale)
            eq_(u'Firefox', feedback.product)
            eq_(u'14.0.1', feedback.version)

        finally:
            # FIXME - We have to do another request to set the
            # LocalizingClient back to en-US otherwise it breaks all
            # tests ever. This is goofy-pants since it should get
            # reset in test teardown.
            resp = self.client.get('/en-US/feedback/')

    def test_urls_product(self):
        """Test setting product from the url"""
        amount = models.Response.objects.count()

        ua = 'Mozilla/5.0 (Android; Tablet; rv:24.0) Gecko/24.0 Firefox/24.0'
        url = reverse('feedback', args=(u'android',))
        data = {
            'happy': 1,
            'description': u'Firefox rocks FFA!',
            'url': u'http://mozilla.org/'
        }
        resp = self.client.post(url, data, HTTP_USER_AGENT=ua)
        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        # Product comes from the url
        eq_(u'Firefox for Android', feedback.product)
        # Since product in user agent matches url, we set the version,
        # too.
        eq_(u'24.0', feedback.version)
        eq_(u'', feedback.channel)

    def test_urls_product_version(self):
        """Test setting version from the url"""
        amount = models.Response.objects.count()

        url = reverse('feedback', args=(u'android', u'29'))
        resp = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks FFA 29!',
            'url': u'http://mozilla.org/'
        })

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox for Android', feedback.product)
        eq_(u'29', feedback.version)
        eq_(u'', feedback.channel)

    def test_urls_product_version_channel(self):
        """Test setting channel from url"""
        amount = models.Response.objects.count()

        url = reverse('feedback', args=(u'android', u'29', u'nightly'))
        resp = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks FFA 29 nightly!',
            'url': u'http://mozilla.org/'
        })

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox for Android', feedback.product)
        eq_(u'29', feedback.version)
        eq_(u'nightly', feedback.channel)

    def test_urls_product_version_uppercased_channel(self):
        """Test setting uppercase channel from the url gets lowercased"""
        amount = models.Response.objects.count()

        url = reverse('feedback', args=(u'android', u'29', u'NIGHTLY'))
        resp = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks FFA 29 NIGHTLY!',
            'url': u'http://mozilla.org/'
        })

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox for Android', feedback.product)
        eq_(u'29', feedback.version)
        eq_(u'nightly', feedback.channel)

    def test_urls_product_version_channel_android_ua(self):
        """Test setting everything with a Fennec user agent"""
        amount = models.Response.objects.count()

        ua = 'Mozilla/5.0 (Android; Tablet; rv:24.0) Gecko/24.0 Firefox/24.0'
        url = reverse('feedback', args=(u'android', u'29', u'nightly'))
        resp = self.client.post(
            url,
            {
                'happy': 1,
                'description': u'Firefox rocks FFA 29 nightly android ua!',
                'url': u'http://mozilla.org/'
            },
            HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox for Android', feedback.product)
        eq_(u'29', feedback.version)
        eq_(u'nightly', feedback.channel)

    def test_urls_product_inferred_platform(self):
        """Test setting product from the url and platform inference"""
        amount = models.Response.objects.count()

        # Test that we infer the platform if the products are the
        # same.
        ua = 'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1'  # noqa
        url = reverse('feedback', args=(u'firefox',))
        resp = self.client.post(
            url,
            {
                'happy': 1,
                'description': u'Firefox rocks FFA!',
                'url': u'http://mozilla.org/'
            },
            HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox', feedback.product)
        eq_(u'Windows Vista', feedback.browser_platform)

    def test_urls_product_inferred_platform_firefoxdev(self):
        """Test firefoxdev platform gets inferred"""
        prod = ProductFactory(
            display_name=u'Firefox dev',
            db_name=u'Firefox dev',
            slug=u'firefoxdev',
            enabled=True,
        )

        amount = models.Response.objects.count()

        # Test that we infer the platform if the products are the
        # same.
        ua = 'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1'  # noqa
        url = reverse('feedback', args=(prod.slug,))
        resp = self.client.post(
            url,
            {
                'happy': 1,
                'description': u'Firefox rocks FFA!',
                'url': u'http://mozilla.org/'
            },
            HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox dev', feedback.product)
        eq_(u'Windows Vista', feedback.browser_platform)

    def test_urls_product_not_inferred_platform_firefoxdev(self):
        """Test firefoxdev platform doesn't get inferred if not Firefox"""
        prod = ProductFactory(
            display_name=u'Firefox dev',
            db_name=u'Firefox dev',
            slug=u'firefoxdev',
            enabled=True,
        )

        amount = models.Response.objects.count()

        # If the user agent is IE, then don't infer the platform.
        ua = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)'  # noqa
        url = reverse('feedback', args=(prod.slug,))
        resp = self.client.post(
            url,
            {
                'happy': 1,
                'description': u'Firefox rocks FFA!',
                'url': u'http://mozilla.org/'
            },
            HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox dev', feedback.product)
        eq_(u'', feedback.browser_platform)

    def test_urls_product_no_inferred_platform(self):
        """Test setting product from the url and platform non-inference"""
        prod = ProductFactory(
            display_name=u'Someprod',
            db_name=u'Someprod',
            slug=u'someprod',
            enabled=True,
        )

        amount = models.Response.objects.count()

        # The UA is for a different browser than what the user is
        # leaving feedback for, so we should not infer the platform.
        ua = 'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1'  # noqa
        url = reverse('feedback', args=(prod.slug,))
        resp = self.client.post(
            url,
            {
                'happy': 1,
                'description': u'Firefox rocks FFA!',
                'url': u'http://mozilla.org/'
            },
            HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Someprod', feedback.product)
        eq_(u'', feedback.platform)

    def test_infer_version_if_product_matches(self):
        """Infer the version from the user agent if products match"""
        amount = models.Response.objects.count()

        # Test that we infer the platform if the products are the
        # same.
        ua = 'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1'  # noqa
        url = reverse('feedback', args=(u'firefox',))
        data = {
            'happy': 1,
            'description': u'Firefox rocks FFA!',
            'url': u'http://mozilla.org/'
        }
        resp = self.client.post(url, data, HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox', feedback.product)
        eq_(u'14.0.1', feedback.version)
        eq_(u'Windows Vista', feedback.platform)

    def test_dont_infer_version_if_product_doesnt_match(self):
        """Don't infer version from the user agent if product doesn't match"""
        amount = models.Response.objects.count()

        # Using a Firefox for Android browser to leave feedback for Firefox
        # Desktop.
        ua = 'Mozilla/5.0 (Android; Tablet; rv:24.0) Gecko/24.0 Firefox/24.0'
        url = reverse('feedback', args=(u'firefox',))
        data = {
            'happy': 1,
            'description': u'Firefox rocks FFA!',
            'url': u'http://mozilla.org/'
        }
        resp = self.client.post(url, data, HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        eq_(amount + 1, models.Response.objects.count())
        feedback = models.Response.objects.latest(field_name='id')
        eq_(u'en-US', feedback.locale)
        eq_(u'Firefox', feedback.product)
        eq_(u'', feedback.version)
        eq_(u'', feedback.platform)

    def test_invalid_form(self):
        """Bad data gets ignored. Thanks!"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/'
            # No happy/sad
            # No description
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 0)

    def test_invalid_form_happy(self):
        """Bad data gets ignored. Thanks!"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0
            # No description
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 0)

    def test_invalid_form_sad(self):
        """Bad data gets ignored. Thanks!"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 1
            # No description
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 0)

    def test_whitespace_description(self):
        """Descriptions with just whitespace get thrown out"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0,
            'description': u'      '
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 0)

    def test_unicode_in_description(self):
        """Description should accept unicode data"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0,
            'description': u'\u2713 this works'
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 1)

    def test_unicode_in_url(self):
        """URL should accept unicode data"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': u'http://mozilla.org/\u2713',
            'happy': 0,
            'description': u'foo'
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 1)

    def test_valid_urls(self):
        """Test valid url field values"""
        test_data = [
            # input, expected
            ('example.com', 'http://example.com/'),
            ('http://example.com', 'http://example.com/'),
            ('https://example.com', 'https://example.com/'),
            ('ftp://example.com', ''),  # We currently redact ftp urls
            ('about:config', 'about:config'),
            ('chrome://foo', 'chrome://foo')
        ]

        url = reverse('feedback', args=(u'firefox',))
        for item, expected in test_data:
            cache.clear()

            r = self.client.post(url, {
                'url': item,
                'happy': 0,
                'description': u'foo' + item
            })

            self.assertRedirects(r, reverse('thanks'))
            latest = models.Response.uncached.latest('pk')
            eq_(latest.url, expected)

    def test_url_cleaning(self):
        """Clean urls before saving"""
        url = reverse('feedback', args=(u'firefox',))
        self.client.post(url, {
            'url': u'http://mozilla.org:8000/path/?foo=bar#bar',
            'happy': 0,
            'description': u'foo'
        })
        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.url, u'http://mozilla.org/path/')

    def test_email_collection(self):
        """If the user enters an email and checks the box, collect email."""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u"I like the colors.",
            'email': 'bob@example.com',
            'email_ok': 'on',
        })
        eq_(models.ResponseEmail.objects.count(), 1)
        eq_(r.status_code, 302)

    def test_email_privacy(self):
        """If an email is entered, but box is not checked, don't collect."""
        email_count = models.ResponseEmail.objects.count()

        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u"I like the colors.",
            'email': 'bob@example.com',
            'email_ok': '',
        })
        eq_(email_count, models.ResponseEmail.objects.count())
        eq_(r.status_code, 302)

    def test_email_missing(self):
        """If no email, ignore it."""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u'Can you fix it?',
            'email_ok': 'on',
        })
        eq_(models.Response.objects.count(), 1)
        eq_(models.ResponseEmail.objects.count(), 0)
        assert not models.ResponseEmail.objects.exists()
        eq_(r.status_code, 302)

    def test_email_invalid(self):
        """If email_ok box is checked, but bad email or no email, ignore it."""
        url = reverse('feedback', args=(u'firefox',))

        # Invalid email address gets ignored, but response is
        # otherwise saved.
        r = self.client.post(url, {
            'happy': 0,
            'description': u'There is something wrong here.\0',
            'email_ok': 'on',
            'email': '/dev/sda1\0',
        })
        assert not models.ResponseEmail.objects.exists()
        eq_(r.status_code, 302)

        # Invalid email address is ignored if email_ok box is not
        # checked.
        r = self.client.post(url, {
            'happy': 0,
            'description': u'There is something wrong here.\0',
            'email_ok': '',
            'email': "huh what's this for?",
        })
        assert not models.ResponseEmail.objects.exists()
        # Bad email if the box is not checked is not an error.
        eq_(r.status_code, 302)

    def test_src_to_source(self):
        """We capture the src querystring arg in the source column"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?src=newsletter', {
            'happy': 0,
            'description': u"I like the colors.",
        })

        self.assertRedirects(r, reverse('thanks'))

        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.source, u'newsletter')

    def test_utm_source_to_source(self):
        """We capture the utm_source querystring arg in the source column"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?utm_source=newsletter', {
            'happy': 0,
            'description': u"I like the colors.",
        })

        self.assertRedirects(r, reverse('thanks'))

        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.source, u'newsletter')

    def test_utm_campaign_to_source(self):
        """We capture the utm_campaign querystring arg in the source column"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?utm_campaign=20140220_email', {
            'happy': 0,
            'description': u"I like the colors.",
        })

        self.assertRedirects(r, reverse('thanks'))

        feedback = models.Response.objects.latest(field_name='id')
        eq_(feedback.campaign, u'20140220_email')

    def test_save_context_basic(self):
        """We capture any querystring vars as context"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?foo=bar', {
            'happy': 0,
            'description': u"I like the colors.",
        })

        self.assertRedirects(r, reverse('thanks'))

        context = models.ResponseContext.objects.latest(field_name='id')
        eq_(context.data, {'foo': 'bar'})

    def test_save_context_long_key(self):
        """Long keys are truncated"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?foo12345678901234567890=bar', {
            'happy': 0,
            'description': u"I like the colors.",
        })

        self.assertRedirects(r, reverse('thanks'))

        context = models.ResponseContext.objects.latest(field_name='id')
        eq_(context.data, {'foo12345678901234567': 'bar'})

    def test_save_context_long_val(self):
        """Long values are truncated"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?foo=' + ('a' * 100) + 'b', {
            'happy': 0,
            'description': u"I like the colors.",
        })

        self.assertRedirects(r, reverse('thanks'))

        context = models.ResponseContext.objects.latest(field_name='id')
        eq_(context.data, {'foo': ('a' * 100)})

    def test_save_context_maximum_pairs(self):
        """Only save 20 pairs"""
        url = reverse('feedback', args=(u'firefox',))

        qs = '&'.join(['foo%02d=%s' % (i, i) for i in range(25)])

        r = self.client.post(url + '?' + qs, {
            'happy': 0,
            'description': u"I like the colors.",
        })

        self.assertRedirects(r, reverse('thanks'))

        context = models.ResponseContext.objects.latest(field_name='id')
        data = sorted(context.data.items())
        eq_(len(data), 20)
        eq_(data[0], (u'foo00', '0'))
        eq_(data[-1], (u'foo19', '19'))


class TestDeprecatedAndroidFeedback(TestCase):
    client_class = LocalizingClient

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
        eq_(u'24.0', feedback.version)

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
        eq_(u'24.0', feedback.version)

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
        eq_(u'24.0', feedback.version)

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
        eq_(u'24.0', feedback.version)

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
        eq_(feedback.browser, u'')
        eq_(feedback.browser_version, u'')
        eq_(feedback.platform, u'')

        # This comes from the client.post url.
        eq_(u'en-US', feedback.locale, u'en-US')
        # This comes from the user agent from the LocalizingClient
        eq_(feedback.product, u'')
        eq_(feedback.channel, u'')
        eq_(feedback.version, u'')


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


class TestCSRF(TestCase):
    def setUp(self):
        super(TestCSRF, self).setUp()
        self.factory = RequestFactory()
        self.client = LocalizingClient(enforce_csrf_checks=True)

    def test_no_csrf_regular_form_fails(self):
        """No csrf token in post data from anonymous user yields 403."""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks!',
            'url': u'http://mozilla.org/'
        })

        eq_(r.status_code, 403)

    def test_firefox_for_android(self):
        """No csrf token for a FfA post works fine."""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            '_type': 1,
            'description': u'Firefox rocks!',
            'add_url': 1,
            'url': u'http://mozilla.org/'
        })
        eq_(r.status_code, 302)


class TestWebFormThrottling(TestCase):
    client_class = LocalizingClient

    def test_throttled(self):
        """Verify that posts are throttled."""
        # Make sure there are no responses in the db because we're
        # basing our test on response counts.
        initial_amount = models.Response.objects.count()
        eq_(initial_amount, 0)

        url = reverse('feedback', args=(u'firefox',))

        # Toss 100 responses in.
        for i in range(100):
            r = self.client.post(url, {
                'happy': 1,
                'description': u'{0} Firefox rocks! {0}'.format(i),
                'url': u'http://mozilla.org/'
            })
        eq_(models.Response.objects.count(), 50)

        # The 101st should be throttled, so there should only be 100
        # responses in the db.
        r = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks!',
            'url': u'http://mozilla.org/'
        })
        eq_(models.Response.objects.count(), 50)

        # Make sure we still went to the Thanks page.
        self.assertRedirects(r, reverse('thanks'))

    def test_double_submit_throttling(self):
        """Verify double-submit throttling."""
        # Make sure there are no responses in the db because we're
        # basing our test on response counts.
        initial_amount = models.Response.objects.count()
        eq_(initial_amount, 0)

        url = reverse('feedback', args=(u'firefox',))

        data = {
            'happy': 1,
            'description': u'Double-submit is the best!',
            'url': u'http://mozilla.org/'
        }

        # Post it!
        r = self.client.post(url, data)
        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 1)

        # Post it again! This time it doesn't get to the db.
        r = self.client.post(url, data)
        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 1)

        # Post something different from the same ip address.
        data['description'] = u'Not a double-submit!'
        r = self.client.post(url, data)
        self.assertRedirects(r, reverse('thanks'))
        eq_(models.Response.objects.count(), 2)
