import datetime

from fjord.base.tests import eq_, TestCase
from fjord.feedback.tests import ResponseFactory
from fjord.suggest import get_suggesters
from fjord.suggest.utils import get_suggestions
from fjord.suggest.providers.dummy import DummySuggester
from fjord.suggest.tests import SuggesterTestMixin


class DummySuggesterLoadingTestCase(SuggesterTestMixin, TestCase):
    suggesters = []

    def test_didnt_load(self):
        dummy_providers = [
            prov for prov in get_suggesters()
            if isinstance(prov, DummySuggester)
        ]
        eq_(len(dummy_providers), 0)


class DummySuggesterTestCase(SuggesterTestMixin, TestCase):
    suggesters = [
        'fjord.suggest.providers.dummy.DummySuggester'
    ]

    def test_load(self):
        dummy_providers = [
            prov for prov in get_suggesters()
            if isinstance(prov, DummySuggester)
        ]
        eq_(len(dummy_providers), 1)

    def test_get_suggestions(self):
        now = u'ts_{0}'.format(datetime.datetime.now())

        req = self.get_feedback_post_request({
            'happy': 1,
            'description': now,
            'url': u'http://example.com/{0}'.format(now)
        })
        feedback = ResponseFactory(
            happy=True,
            description=now,
            url=u'http://example.com/{0}'.format(now)
        )

        # Try with just the feedback
        links = get_suggestions(feedback)
        eq_(len(links), 1)
        eq_(links[0].provider, 'dummy')
        eq_(links[0].provider_version, 1)
        eq_(links[0].cssclass, u'document')
        eq_(links[0].summary, u'summary {0}'.format(now)),
        eq_(links[0].description, u'description {0}'.format(now))
        eq_(links[0].url, feedback.url)

        # Now with the feedback and request
        links = get_suggestions(feedback, req)
        eq_(len(links), 1)
        eq_(links[0].provider, 'dummy')
        eq_(links[0].provider_version, 1)
        eq_(links[0].cssclass, u'document')
        eq_(links[0].summary, u'summary {0}'.format(now)),
        eq_(links[0].description, u'description {0}'.format(now))
        eq_(links[0].url, feedback.url)
