from fjord.base.tests import (
    LocalizingClient,
    reverse,
    TestCase,
)
from fjord.feedback.tests import ResponseFactory
from fjord.redirector import build_redirect_url
from fjord.redirector.tests import RedirectorTestMixin
from fjord.suggest.providers.trigger.provider import (
    format_redirect,
    interpolate_url,
    PROVIDER,
    PROVIDER_VERSION
)
from fjord.suggest.providers.trigger.tests import TriggerRuleFactory
from fjord.suggest.tests import SuggesterTestMixin


class InterpolateTestCase(TestCase):
    def test_no_interpolation(self):
        resp = ResponseFactory()
        url = interpolate_url('http://example.com', resp)
        assert url == 'http://example.com'

    def test_interpolation(self):
        resp = ResponseFactory(
            happy=True,
            product=u'Firefox',
            version=u'38.0',
            platform=u'Windows 8.1',
        )
        url = interpolate_url(
            'http://example.com?' +
            'happy={HAPPY}&' +
            'product={PRODUCT}&' +
            'version={VERSION}&' +
            'platform={PLATFORM}',
            resp
        )
        assert (
            url ==
            ('http://example.com?' +
             'happy=happy&' +
             'product=Firefox&' +
             'version=38.0&' +
             'platform=Windows+8.1')
        )

    def test_empty_values(self):
        resp = ResponseFactory(
            happy=False,
            product=u'',
            version=u'',
            platform=u'',
        )
        url = interpolate_url(
            'http://example.com?' +
            'happy={HAPPY}&' +
            'product={PRODUCT}&' +
            'version={VERSION}&' +
            'platform={PLATFORM}',
            resp
        )
        assert (
            url ==
            ('http://example.com?' +
             'happy=sad&' +
             'product=&' +
             'version=&' +
             'platform=')
        )

    def test_unicode(self):
        resp = ResponseFactory(
            happy=True,
            platform=u'unicode \xca',
        )
        url = interpolate_url(
            'http://example.com?platform={PLATFORM}',
            resp
        )
        assert (
            url ==
            'http://example.com?platform=unicode+%C3%8A'
        )

    def test_quoting(self):
        badchars = '?"\'&='
        resp = ResponseFactory(
            happy=False,
            product=badchars,
            version=badchars,
            platform=badchars,
        )
        url = interpolate_url(
            'http://example.com?' +
            'happy={HAPPY}&' +
            'product={PRODUCT}&' +
            'version={VERSION}&' +
            'platform={PLATFORM}',
            resp
        )
        assert (
            url ==
            ('http://example.com?' +
             'happy=sad&' +
             'product=%3F%22%27%26%3D&'
             'version=%3F%22%27%26%3D&'
             'platform=%3F%22%27%26%3D')
        )


class TriggerTestCase(SuggesterTestMixin, RedirectorTestMixin, TestCase):
    client_class = LocalizingClient
    suggesters = [
        'fjord.suggest.providers.trigger.provider.TriggerSuggester'
    ]
    redirectors = [
        'fjord.suggest.providers.trigger.provider.TriggerRedirector'
    ]

    def post_feedback(self, locale, data):
        url = reverse('feedback', args=(u'firefox',), locale=locale)
        return self.client.post(url, data, follow=True)

    def test_get_suggestions_with_request_no_rules(self):
        resp = self.post_feedback(
            locale='en-US',
            data={'happy': 0, 'description': u'rc4 is awesome'}
        )

        links = resp.context['suggestions']

        assert len(links) == 0

    def test_enabled_rule_matches_and_returns_correct_data(self):
        tr = TriggerRuleFactory(locales=['en-US'], is_enabled=True)
        resp = self.post_feedback(
            locale='en-US',
            data={'happy': 0, 'description': u'rc4 is awesome'}
        )

        links = resp.context['suggestions']

        assert len(links) == 1
        assert links[0].provider == PROVIDER
        assert links[0].provider_version == PROVIDER_VERSION
        assert links[0].summary == tr.title
        assert links[0].description == tr.description
        assert links[0].url == build_redirect_url(format_redirect(tr.slug))

    def test_disabled_rule_wont_match(self):
        TriggerRuleFactory(locales=['en-US'], is_enabled=False)
        resp = self.post_feedback(
            locale='en-US',
            data={'happy': 0, 'description': u'rc4 is awesome'}
        )

        links = resp.context['suggestions']

        assert len(links) == 0

    def test_with_multiple_rules(self):
        rules = [
            TriggerRuleFactory(
                sortorder=0, locales=['en-US'], slug='a', is_enabled=False
            ),
            TriggerRuleFactory(
                sortorder=1, locales=['en-US'], slug='b', is_enabled=True
            ),
            TriggerRuleFactory(
                sortorder=2, locales=['en-US'], slug='c', is_enabled=True
            ),
        ]
        resp = self.post_feedback(
            locale='en-US',
            data={'happy': 0, 'description': u'rc4 is awesome'}
        )

        links = resp.context['suggestions']

        # The disabled one won't match, but the other two will match in the
        # sort order.
        assert len(links) == 2
        assert (
            links[0].url == build_redirect_url(format_redirect(rules[1].slug))
        )
        assert (
            links[1].url == build_redirect_url(format_redirect(rules[2].slug))
        )

    def test_sort_order(self):
        # sortorder--not db row order--sets the order of the
        # suggestions.
        rules = [
            TriggerRuleFactory(
                sortorder=10, locales=['en-US'], slug='a', is_enabled=True
            ),
            TriggerRuleFactory(
                sortorder=1, locales=['en-US'], slug='b', is_enabled=True
            ),
        ]
        resp = self.post_feedback(
            locale='en-US',
            data={'happy': 0, 'description': u'rc4 is awesome'}
        )

        links = resp.context['suggestions']

        # The disabled one won't match, but the other two will match in the
        # sort order.
        assert len(links) == 2

        assert (
            links[0].url == build_redirect_url(format_redirect(rules[1].slug))
        )
        assert (
            links[1].url == build_redirect_url(format_redirect(rules[0].slug))
        )

    def test_redirector(self):
        tr = TriggerRuleFactory(url=u'http://example.com/', is_enabled=True)
        resp = self.post_feedback(
            locale='en-US',
            data={'happy': 0, 'description': u'rc4 is awesome'}
        )

        links = resp.context['suggestions']

        assert len(links) == 1
        assert links[0].url == build_redirect_url(format_redirect(tr.slug))

        resp = self.client.get(links[0].url)
        assert resp.status_code == 302
        assert resp.url == 'http://example.com/'

    def test_redirector_templated(self):
        tr = TriggerRuleFactory(
            url=u'http://example.com/?locale={LOCALE}',
            is_enabled=True
        )
        resp = self.post_feedback(
            locale='en-US',
            data={'happy': 0, 'description': u'rc4 is awesome'}
        )

        links = resp.context['suggestions']

        assert len(links) == 1
        assert links[0].url == build_redirect_url(format_redirect(tr.slug))

        resp = self.client.get(links[0].url)
        assert resp.status_code == 302
        assert resp.url == 'http://example.com/?locale=en-US'
