from fjord.base.tests import (
    LocalizingClient,
    reverse,
    TestCase,
)
from fjord.redirector import build_redirect_url
from fjord.redirector.tests import RedirectorTestMixin
from fjord.suggest.providers.trigger.provider import (
    format_redirect,
    PROVIDER,
    PROVIDER_VERSION
)
from fjord.suggest.providers.trigger.tests import TriggerRuleFactory
from fjord.suggest.tests import SuggesterTestMixin


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
