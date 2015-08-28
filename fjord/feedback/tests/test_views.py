import json

from django.core.cache import cache
from django.test.client import RequestFactory
from django.test.utils import override_settings

from fjord.base.tests import (
    LocalizingClient,
    AnalyzerProfileFactory,
    reverse,
    TestCase,
)
from fjord.feedback import models
from fjord.feedback.tests import ProductFactory, ResponseFactory


class TestRedirectFeedback(TestCase):
    client_class = LocalizingClient

    def test_happy_redirect(self):
        r = self.client.get(reverse('happy-redirect'))
        self.assertRedirects(r, reverse('feedback') + '?happy=1')

    def test_sad_redirect(self):
        r = self.client.get(reverse('sad-redirect'))
        self.assertRedirects(r, reverse('feedback') + '?happy=0')


class TestFeedback(TestCase):
    client_class = LocalizingClient

    def test_xframe_header(self):
        """Feedback form should *always* have X-FRAME-OPTIONS: DENY

        This is because the feedback form can do various magic things
        that shouldn't ever be framed.

        """
        url = reverse('feedback', args=(u'firefox',))
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp['X-Frame-Options'] == 'DENY'

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
        assert amount + 1 == models.Response.objects.count()

        feedback = models.Response.objects.latest(field_name='id')
        assert u'Firefox rocks!' == feedback.description
        assert u'http://mozilla.org/' == feedback.url
        assert True == feedback.happy

        # This comes from the client.post url.
        assert u'en-US' == feedback.locale
        # Note: This comes from the user agent from the LocalizingClient
        assert u'Firefox' == feedback.product
        assert u'14.0.1' == feedback.version

        # Make sure it doesn't create an email record
        assert models.ResponseEmail.objects.count() == 0

        # Make sure it doesn't create a context record
        assert models.ResponseContext.objects.count() == 0

    def test_response_id_in_session(self):
        url = reverse('feedback', args=(u'firefox',))
        self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks!',
            'url': u'http://mozilla.org/'
        })
        response = models.Response.objects.order_by('-id')[0]
        assert self.client.session['response_id'] == response.id

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
        assert amount + 1 == models.Response.objects.count()

        feedback = models.Response.objects.latest(field_name='id')
        assert u"Firefox doesn't make me sandwiches. :(" == feedback.description
        assert u'' == feedback.url
        assert False == feedback.happy

        # This comes from the client.post url.
        assert u'en-US' == feedback.locale
        # Note: This comes from the user agent from the LocalizingClient
        assert u'Firefox' == feedback.product
        assert u'14.0.1' == feedback.version

    def test_response_id_in_qs_unauthenticated(self):
        """Verify response_id in querystring is ignored if user is not
        authenticated
        """
        feedback = ResponseFactory()
        url = reverse('thanks') + '?response_id={0}'.format(feedback.id)
        r = self.client.get(url)

        assert r.status_code == 200
        assert r.context['feedback'] == None
        assert r.context['suggestions'] == None

    def test_response_id_in_qs_authenticated(self):
        """Verify response_id in querystring overrides session id"""
        # Create analyzer and log in.

        jane = AnalyzerProfileFactory(user__email='jane@example.com').user
        self.client_login_user(jane)

        # Create some feedback which sets the response_id in the
        # session.
        url = reverse('feedback', args=(u'firefox',), locale='en-US')
        r = self.client.post(url, {
            'happy': 0,
            'description': u'Why Firefox not make me sandwiches!',
        }, follow=True)

        # Create another piece of feedback which is not the one we
        # just did.
        feedback = ResponseFactory(description=u'purple horseshoes')

        # Fetch the thank you page with the response_id in the
        # querystring.
        url = reverse('thanks') + '?response_id={0}'.format(feedback.id)
        r = self.client.get(url)

        assert r.status_code == 200
        assert r.context['feedback'].id == feedback.id
        assert r.context['suggestions'] == []

    def test_happy_prefill_in_querystring_is_ignored(self):
        url = reverse('feedback', args=(u'firefox',), locale='en-US')
        url = url + '?happy=0&foo=bar'
        resp = self.client.post(url, {
            'happy': 1,
            'description': u"Firefox is the best browser I've ever used!",
        })

        assert resp.status_code == 302

        # The url has 0, but the form data is 1, so it should end up as 1.
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.happy == 1

        # "happy=0" should be removed from the querystring before
        # figuring out the context. So "foo=bar" should be in the
        # context, but not "happy=0".
        context = models.ResponseContext.objects.latest(field_name='id')
        assert context.data == {'foo': 'bar'}

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
            count = models.Response.objects.count()

            # Hard-coded url so we're guaranteed to get /es/.
            url = reverse('feedback', args=(u'firefox',), locale='es')
            resp = self.client.post(url, {
                'happy': 1,
                'description': u'Firefox rocks for es!',
                'url': u'http://mozilla.org/'
            })

            self.assertRedirects(resp, reverse('thanks'))
            assert count + 1 == models.Response.objects.count()
            feedback = models.Response.objects.latest(field_name='id')
            assert u'es' == feedback.locale
            assert u'Firefox' == feedback.product
            assert u'14.0.1' == feedback.version

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
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        # Product comes from the url
        assert u'Firefox for Android' == feedback.product
        # Since product in user agent matches url, we set the version,
        # too.
        assert u'24.0' == feedback.version
        assert u'' == feedback.channel

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
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox for Android' == feedback.product
        assert u'29' == feedback.version
        assert u'' == feedback.channel

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
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox for Android' == feedback.product
        assert u'29' == feedback.version
        assert u'nightly' == feedback.channel

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
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox for Android' == feedback.product
        assert u'29' == feedback.version
        assert u'nightly' == feedback.channel

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
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox for Android' == feedback.product
        assert u'29' == feedback.version
        assert u'nightly' == feedback.channel

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
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox' == feedback.product
        assert u'Windows Vista' == feedback.browser_platform

    def test_urls_product_inferred_platform_firefoxdev(self):
        """Test firefoxdev platform gets inferred"""
        amount = models.Response.objects.count()

        # Test that we infer the platform if the products are the
        # same.
        ua = 'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1'  # noqa
        url = reverse('feedback', args=('firefoxdev',))
        resp = self.client.post(
            url,
            {
                'happy': 1,
                'description': u'Firefox rocks FFA!',
                'url': u'http://mozilla.org/'
            },
            HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox dev' == feedback.product
        assert u'Windows Vista' == feedback.browser_platform

    def test_urls_product_inferred_platform_fxios(self):
        """Test firefoxdev platform gets inferred"""
        ProductFactory(
            enabled=True,
            display_name=u'Firefox for iOS',
            db_name=u'Firefox for iOS',
            slug=u'fxios',
            on_dashboard=False,
            on_picker=False,
            browser=u'Firefox for iOS',
        )

        # Test that we infer the platform if the products are the
        # same.
        ua = (
            'Mozilla/5.0 (iPod touch; CPU iPhone OS 8_4 like Mac OS X) '
            'AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0 '
            'Mobile/12H143 Safari/600.1.4'
        )
        url = reverse('feedback', args=('fxios',))
        resp = self.client.post(
            url,
            {
                'happy': 1,
                'description': u'Firefox for iOS rocks!',
                'url': u'http://mozilla.org/'
            },
            HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        assert models.Response.objects.count() == 1
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.locale == 'en-US'
        assert feedback.product == 'Firefox for iOS'
        assert feedback.platform == 'iPhone OS 8.4'
        assert feedback.browser == 'Firefox for iOS'
        assert feedback.browser_version == '1.0'
        assert feedback.browser_platform == 'iPhone OS'

    def test_urls_product_not_inferred_platform_firefoxdev(self):
        """Test firefoxdev platform doesn't get inferred if not Firefox"""
        amount = models.Response.objects.count()

        # If the user agent is IE, then don't infer the platform.
        ua = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)'  # noqa
        url = reverse('feedback', args=('firefoxdev',))
        resp = self.client.post(
            url,
            {
                'happy': 1,
                'description': u'Firefox rocks FFA!',
                'url': u'http://mozilla.org/'
            },
            HTTP_USER_AGENT=ua)

        self.assertRedirects(resp, reverse('thanks'))
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox dev' == feedback.product
        assert u'' == feedback.browser_platform

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
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Someprod' == feedback.product
        assert u'' == feedback.platform

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
        assert amount + 1 == models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox' == feedback.product
        assert u'14.0.1' == feedback.version
        assert u'Windows Vista' == feedback.platform

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
        assert amount + 1, models.Response.objects.count()
        feedback = models.Response.objects.latest(field_name='id')
        assert u'en-US' == feedback.locale
        assert u'Firefox' == feedback.product
        assert u'' == feedback.version
        assert u'' == feedback.platform

    def test_invalid_form(self):
        """Bad data gets ignored. Thanks!"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/'
            # No happy/sad
            # No description
        })

        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 0

    def test_invalid_form_happy(self):
        """Bad data gets ignored. Thanks!"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0
            # No description
        })

        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 0

    def test_invalid_form_sad(self):
        """Bad data gets ignored. Thanks!"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 1
            # No description
        })

        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 0

    def test_whitespace_description(self):
        """Descriptions with just whitespace get thrown out"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0,
            'description': u'      '
        })

        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 0

    def test_unicode_in_description(self):
        """Description should accept unicode data"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/',
            'happy': 0,
            'description': u'\u2713 this works'
        })

        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 1

    def test_unicode_in_url(self):
        """URL should accept unicode data"""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            'url': u'http://mozilla.org/\u2713',
            'happy': 0,
            'description': u'foo'
        })

        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 1

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
            latest = models.Response.objects.latest('pk')
            assert latest.url == expected

    def test_url_cleaning(self):
        """Clean urls before saving"""
        url = reverse('feedback', args=(u'firefox',))
        self.client.post(url, {
            'url': u'http://mozilla.org:8000/path/?foo=bar#bar',
            'happy': 0,
            'description': u'foo'
        })
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.url == u'http://mozilla.org/path/'

    def test_url_leading_trailing_whitespace_removal(self):
        """Leading/trailing whitespace in urls is stripped"""
        url = reverse('feedback', args=(u'firefox',))
        self.client.post(url, {
            'url': u'   \t\n\r',
            'happy': 0,
            'description': u'foo'
        })
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.url == u''

    def test_email_collection(self):
        """If the user enters an email and checks the box, collect email."""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u'I like the colors.',
            'email': 'bob@example.com',
            'email_ok': 'on',
        })
        assert models.ResponseEmail.objects.count() == 1
        assert r.status_code == 302

    def test_email_privacy(self):
        """If an email is entered, but box is not checked, don't collect."""
        email_count = models.ResponseEmail.objects.count()

        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u'I like the colors.',
            'email': 'bob@example.com',
            'email_ok': '',
        })
        assert email_count == models.ResponseEmail.objects.count()
        assert r.status_code == 302

    def test_email_missing(self):
        """If no email, ignore it."""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u'Can you fix it?',
            'email_ok': 'on',
        })
        assert models.Response.objects.count() == 1
        assert models.ResponseEmail.objects.count() == 0
        assert not models.ResponseEmail.objects.exists()
        assert r.status_code == 302

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
        assert r.status_code == 302

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
        assert r.status_code == 302

    def test_browser_data_collection(self):
        """If the user checks the box, collect the browser data."""
        url = reverse('feedback', args=(u'firefox',))
        browser_data = {'application': 'foo'}

        r = self.client.post(url, {
            'happy': 0,
            'description': u'I like the colors.',
            'browser_ok': 'on',
            'browser_data': json.dumps(browser_data)
        })
        assert r.status_code == 302
        assert models.ResponsePI.objects.count() == 1
        rti = models.ResponsePI.objects.latest('id')
        assert rti.data == browser_data

    def test_browser_data_not_ok(self):
        """If the user doesn't check the box, don't collect data."""
        # Note: We shouldn't ever be in this situation since the form
        # only adds the browser data when the user checks the box and
        # when they uncheck the box, the form removes it. This test is
        # here in case that code is busted.
        url = reverse('feedback', args=(u'firefox',))
        browser_data = {'application': 'foo'}

        r = self.client.post(url, {
            'happy': 0,
            'description': u'I like the colors.',
            'browser_ok': '',
            'browser_data': json.dumps(browser_data)
        })
        assert r.status_code == 302
        assert models.ResponsePI.objects.count() == 0

    def test_browser_data_invalid(self):
        """If browser_data is not valid json, don't collect it."""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u'I like the colors.',
            'browser_ok': 'on',
            'browser_data': 'invalid json'
        })
        assert r.status_code == 302
        assert models.ResponsePI.objects.count() == 0

    def test_browser_data_there_for_product_as_firefox(self):
        # Feedback for ProductFoo should collect browser data if the browser
        # being used is "Firefox".
        prod = ProductFactory(
            display_name=u'ProductFoo',
            slug=u'productfoo',
            enabled=True,
            browser_data_browser=u'Firefox'
        )

        ua = 'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0'
        resp = self.client.get(
            reverse('feedback', args=(prod.slug,)),
            HTTP_USER_AGENT=ua
        )
        assert 'browser-ask' in resp.content

    def test_browser_data_not_there_for_product_no_collection(self):
        # Feedback for ProductFoo should not collect browser data
        # because the product doesn't collect browser data for any
        # browser since the default for browser_data_browser is empty
        # string.
        prod = ProductFactory(
            display_name=u'ProductFoo',
            slug=u'productfoo',
            enabled=True
        )

        ua = 'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0'
        resp = self.client.get(
            reverse('feedback', args=(prod.slug,)),
            HTTP_USER_AGENT=ua
        )
        assert 'browser-ask' not in resp.content

    def test_browser_data_not_there_for_product_wrong_browser(self):
        # Feedback for ProductFoo should not collect browser data if
        # the browser being used doesn't match the browser it should
        # collect browser data for.
        prod = ProductFactory(
            display_name=u'ProductFoo',
            slug=u'productfoo',
            enabled=True,
            browser_data_browser=u'Android'
        )

        ua = 'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0'
        resp = self.client.get(
            reverse('feedback', args=(prod.slug,)),
            HTTP_USER_AGENT=ua
        )
        assert 'browser-ask' not in resp.content

    def test_src_to_source(self):
        """We capture the src querystring arg in the source column"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?src=newsletter', {
            'happy': 0,
            'description': u'I like the colors.',
        })

        self.assertRedirects(r, reverse('thanks'))

        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.source == u'newsletter'

    def test_utm_source_to_source(self):
        """We capture the utm_source querystring arg in the source column"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?utm_source=newsletter', {
            'happy': 0,
            'description': u'I like the colors.',
        })

        self.assertRedirects(r, reverse('thanks'))

        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.source == u'newsletter'

    def test_utm_campaign_to_source(self):
        """We capture the utm_campaign querystring arg in the source column"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?utm_campaign=20140220_email', {
            'happy': 0,
            'description': u'I like the colors.',
        })

        self.assertRedirects(r, reverse('thanks'))

        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.campaign == u'20140220_email'

    def test_save_context_basic(self):
        """We capture any querystring vars as context"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?foo=bar', {
            'happy': 0,
            'description': u'I like the colors.',
        })

        self.assertRedirects(r, reverse('thanks'))

        context = models.ResponseContext.objects.latest(field_name='id')
        assert context.data == {'foo': 'bar'}

    def test_save_context_long_key(self):
        """Long keys are truncated"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?foo12345678901234567890=bar', {
            'happy': 0,
            'description': u'I like the colors.',
        })

        self.assertRedirects(r, reverse('thanks'))

        context = models.ResponseContext.objects.latest(field_name='id')
        assert context.data == {'foo12345678901234567': 'bar'}

    def test_save_context_long_val(self):
        """Long values are truncated"""
        url = reverse('feedback', args=(u'firefox',))

        r = self.client.post(url + '?foo=' + ('a' * 100) + 'b', {
            'happy': 0,
            'description': u'I like the colors.',
        })

        self.assertRedirects(r, reverse('thanks'))

        context = models.ResponseContext.objects.latest(field_name='id')
        assert context.data == {'foo': ('a' * 100)}

    def test_save_context_maximum_pairs(self):
        """Only save 20 pairs"""
        url = reverse('feedback', args=(u'firefox',))

        qs = '&'.join(['foo%02d=%s' % (i, i) for i in range(25)])

        r = self.client.post(url + '?' + qs, {
            'happy': 0,
            'description': u'I like the colors.',
        })

        self.assertRedirects(r, reverse('thanks'))

        context = models.ResponseContext.objects.latest(field_name='id')
        data = sorted(context.data.items())
        assert len(data) == 20
        assert data[0] == (u'foo00', '0')
        assert data[-1] == (u'foo19', '19')


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
        assert r.status_code == 302
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.happy == True
        assert feedback.url == data['url']
        assert feedback.description == data['description']
        assert feedback.device == data['device']
        assert feedback.manufacturer == data['manufacturer']

        # This comes from the client.post url.
        assert u'en-US' == feedback.locale
        # Note: This comes from the user agent from the LocalizingClient
        assert u'Firefox for Android' == feedback.product
        assert u'24.0' == feedback.version

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
        assert r.status_code == 302
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.happy == False
        assert feedback.url == data['url']
        assert feedback.description == data['description']

        # This comes from the client.post url.
        assert u'en-US' == feedback.locale
        # Note: This comes from the user agent from the LocalizingClient
        assert u'Firefox for Android' == feedback.product
        assert u'24.0' == feedback.version

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
        assert r.status_code == 302
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.happy == False
        assert feedback.url == data['url']
        assert feedback.description == data['description']

        # This comes from the client.post url.
        assert u'en-US' == feedback.locale
        # Note: This comes from the user agent from the LocalizingClient
        assert u'Firefox for Android' == feedback.product
        assert u'24.0' == feedback.version

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
        assert r.status_code == 302
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.happy == True
        assert feedback.url == u''
        assert feedback.description == data['description']

        # This comes from the client.post url.
        assert u'en-US' == feedback.locale
        # Note: This comes from the user agent from the LocalizingClient
        assert u'Firefox for Android' == feedback.product
        assert u'24.0' == feedback.version

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
        assert r.status_code == 302
        feedback = models.Response.objects.latest(field_name='id')
        assert feedback.browser == u''
        assert feedback.browser_version == u''
        assert feedback.platform == u''

        # This comes from the client.post url.
        assert ( u'en-US' == feedback.locale, u'en-US')
        # This comes from the user agent from the LocalizingClient
        assert feedback.product == u''
        assert feedback.channel == u''
        assert feedback.version == u''


class TestPicker(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        # FIXME: We can nix this when we stop doing data migrations in
        # test setup.
        models.Product.objects.all().delete()

    def test_picker_no_products(self):
        resp = self.client.get(reverse('feedback'))

        assert resp.status_code == 200
        self.assertTemplateUsed(resp, 'feedback/picker.html')
        assert 'No products available.' in resp.content

    def test_picker_with_products(self):
        ProductFactory(display_name=u'ProductFoo', slug=u'productfoo')
        ProductFactory(display_name=u'ProductBar', slug=u'productbar')

        cache.clear()

        resp = self.client.get(reverse('feedback'))

        assert resp.status_code == 200

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

        assert resp.status_code == 200

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

        assert resp.status_code == 200

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

        assert r.status_code == 403

    def test_firefox_for_android(self):
        """No csrf token for a FfA post works fine."""
        url = reverse('feedback', args=(u'firefox',))
        r = self.client.post(url, {
            '_type': 1,
            'description': u'Firefox rocks!',
            'add_url': 1,
            'url': u'http://mozilla.org/'
        })
        assert r.status_code == 302


class TestWebFormThrottling(TestCase):
    client_class = LocalizingClient

    def test_throttled(self):
        """Verify that posts are throttled."""
        # Make sure there are no responses in the db because we're
        # basing our test on response counts.
        initial_amount = models.Response.objects.count()
        assert initial_amount == 0

        url = reverse('feedback', args=(u'firefox',))

        # Toss 100 responses in.
        for i in range(100):
            r = self.client.post(url, {
                'happy': 1,
                'description': u'{0} Firefox rocks! {0}'.format(i),
                'url': u'http://mozilla.org/'
            })
        assert models.Response.objects.count() == 50

        # The 101st should be throttled, so there should only be 100
        # responses in the db.
        r = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks!',
            'url': u'http://mozilla.org/'
        })
        assert models.Response.objects.count() == 50

        # Make sure we still went to the Thanks page.
        self.assertRedirects(r, reverse('thanks'))

    def test_double_submit_throttling(self):
        """Verify double-submit throttling."""
        # Make sure there are no responses in the db because we're
        # basing our test on response counts.
        initial_amount = models.Response.objects.count()
        assert initial_amount == 0

        url = reverse('feedback', args=(u'firefox',))

        data = {
            'happy': 1,
            'description': u'Double-submit is the best!',
            'url': u'http://mozilla.org/'
        }

        # Post it!
        r = self.client.post(url, data)
        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 1

        # Post it again! This time it doesn't get to the db.
        r = self.client.post(url, data)
        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 1

        # Post something different from the same ip address.
        data['description'] = u'Not a double-submit!'
        r = self.client.post(url, data)
        self.assertRedirects(r, reverse('thanks'))
        assert models.Response.objects.count() == 2
