import os

from mock import MagicMock, patch
import pytest
import requests_mock

from fjord.base.google_utils import GOOGLE_API_URL
from fjord.base.tests import (
    LocalizingClient,
    reverse,
    TestCase,
)
from fjord.feedback.tests import ResponseFactory
from fjord.suggest.providers.sumo import SUMOSuggest
from fjord.suggest.providers.sumo.provider import (
    SUMO_AAQ_URL,
    SUMO_HOST,
    SUMO_SUGGEST_API_URL,
    SUMO_SUGGEST_SESSION_KEY,
)
from fjord.suggest.tests import SuggesterTestMixin
from fjord.redirector.tests import RedirectorTestMixin


class SUMOTestCase(TestCase):
    suggester = SUMOSuggest()

    def test_not_sad(self):
        with requests_mock.Mocker():
            feedback = ResponseFactory(
                happy=True,  # Happy
                locale=u'en-US',
                product=u'Firefox',
                description=u'Firefox does not make good sandwiches. Srsly.'
            )
            links = self.suggester.get_suggestions(feedback)
            assert len(links) == 0

    def test_not_en_us(self):
        with requests_mock.Mocker():
            feedback = ResponseFactory(
                happy=False,
                locale=u'fr',
                product=u'Firefox',
                description=u'Firefox does not make good sandwiches. Srsly.'
            )
            links = self.suggester.get_suggestions(feedback)
            assert len(links) == 0

    def test_not_firefox(self):
        with requests_mock.Mocker():
            feedback = ResponseFactory(
                happy=False,
                locale=u'en-US',
                product=u'Firefox for Android',
                description=u'Firefox does not make good sandwiches. Srsly.'
            )
            links = self.suggester.get_suggestions(feedback)
            assert len(links) == 0

    def test_too_short(self):
        with requests_mock.Mocker():
            feedback = ResponseFactory(
                happy=False,
                locale=u'en-US',
                product=u'Firefox',
                description=u'Firefox is bad.'
            )
            links = self.suggester.get_suggestions(feedback)
            assert len(links) == 0

    def test_not_json(self):
        # If we get back text and not JSON, then the sumo search
        # suggest provider should return no links. This tests the "if
        # any exception happens, return nothing" handling.
        with requests_mock.Mocker() as m:
            m.get(SUMO_SUGGEST_API_URL, text='Gah! Something bad happened')

            patch_point = 'fjord.suggest.providers.sumo.provider.logger'
            with patch(patch_point) as logger_patch:
                # Create a mock that we can call .exception() on and
                # it makes sure it got called.
                logger_patch.exception = MagicMock()

                feedback = ResponseFactory(
                    happy=False,
                    locale=u'en-US',
                    product=u'Firefox',
                    description=(
                        u'slow browser please speed improve i am wait '
                        u'speed improv'
                    )
                )

                links = self.suggester.get_suggestions(feedback)

                # Make sure we get back no links.
                assert len(links) == 0

                # Make sure logger.exception() got called once.
                assert logger_patch.exception.call_count == 1


class SuggestWithRequestTestCase(SuggesterTestMixin, RedirectorTestMixin,
                                 TestCase):
    client_class = LocalizingClient
    suggesters = [
        'fjord.suggest.providers.sumo.SUMOSuggest'
    ]
    redirectors = [
        'fjord.suggest.providers.sumo.SUMOSuggestRedirector'
    ]

    def test_mocked_get_suggestions(self):
        """Tests the whole thing with mocked API calls"""
        sumo_api_ret = {
            'documents': [
                {
                    'id': 12345,
                    'locale': 'en-US',
                    'products': ['firefox'],
                    'slug': 'firefox-uses-too-much-memory-ram',
                    'title': 'Firefox uses too much memory',
                    'summary': 'This article describes how to fix',
                    'html': '<p>Why Firefox uses too much memory</p>',
                    'topics': ['slowness-or-hanging'],
                    'url': '/en-US/kb/firefox-uses-too-much-memory-ram',
                },
                {
                    'id': 12346,
                    'locale': 'en-US',
                    'products': ['firefox'],
                    'slug': 'firefox-takes-long-time-start-up',
                    'title': 'Firefox can take a long time to start up',
                    'summary': 'This article describes how to fix',
                    'html': '<p>Why Firefox could have long startup times</p>',
                    'topics': ['slowness-or-hanging'],
                    'url': '/en-US/kb/firefox-takes-long-time-start-up',
                },
                {
                    'id': 12347,
                    'locale': 'en-US',
                    'products': ['firefox'],
                    'slug': 'firefox--cant-load-sites',
                    'title': 'Firefox sometimes can\'t load sites',
                    'summary': 'This article describes how to fix',
                    'html': (
                        '<p>Possible reasons Firefox can\'t load sites</p>'
                    ),
                    'topics': ['slowness-or-hanging'],
                    'url': '/en-US/kb/firefox-cant-load-sites',
                }
            ]
        }

        with requests_mock.Mocker() as m:
            m.get(SUMO_SUGGEST_API_URL, json=sumo_api_ret)
            m.post(GOOGLE_API_URL, text='whatever')

            url = reverse('feedback', args=(u'firefox',))
            desc = u'slow browser please speed improve i am wait speed improv'

            # Post some basic feedback that meets the SUMO Suggest
            # Provider standards and follow through to the Thank You
            # page. This triggers the suggestions and docs should be
            # in the session.
            resp = self.client.post(url, {
                'happy': 0,
                'description': desc,
            }, follow=True)

            feedback_id = self.client.session['response_id']
            session_key = SUMO_SUGGEST_SESSION_KEY.format(feedback_id)

            # Check the docs in the session. Abuse the fact that we
            # know what order the docs are in since we're mocking.
            docs = self.client.session[session_key]
            for i in range(3):
                doc = docs[i]
                ret_doc = sumo_api_ret['documents'][i]
                assert doc['url'] == SUMO_HOST + ret_doc['url']
                assert doc['summary'] == ret_doc['title']
                assert doc['description'] == ret_doc['summary']

            links = resp.context['suggestions']

            # Abuse the fact that we know what order the links are in
            # since we're mocking.
            for i, link in enumerate(links):
                if i == 3:
                    # This is the aaq link.
                    assert link.cssclass == u'support'
                    assert link.provider == 'sumosuggest'
                    assert link.provider_version == 1
                    assert link.url == '/redirect?r=sumosuggest.aaq'

                    # Fetch the link and make sure it redirects to the
                    # right place.
                    resp = self.client.get(link.url)
                    # Temporary redirect.
                    assert resp.status_code == 302
                    # Redirects to the actual SUMO url.
                    assert resp['Location'] == SUMO_AAQ_URL

                else:
                    # This is a kb link.
                    ret_doc = sumo_api_ret['documents'][i]
                    assert link.provider == 'sumosuggest'
                    assert link.provider_version == 1
                    assert link.cssclass == u'document'
                    assert link.url == '/redirect?r=sumosuggest.{0}'.format(i)
                    assert link.summary == ret_doc['title']
                    assert link.description == ret_doc['summary']

                    # Fetch the link and make sure it redirects to the
                    # right place.
                    resp = self.client.get(link.url)
                    # Temporary redirect.
                    assert resp.status_code == 302
                    # Redirects to the actual SUMO url.
                    assert resp['Location'] == docs[i]['url']


@pytest.mark.skipif('LIVE_API' not in os.environ,
                    reason='LIVE_API not in environ')
class LiveSUMOProviderTestCase(SuggesterTestMixin, TestCase):
    """Test it LIVE!

    This only executes if LIVE_API is defined in the environment.
    Otherwise we skip it.

    This makes it easier to test against what SUMO is actually doing to
    aid debugging issues in the future.

    """
    client_class = LocalizingClient
    suggesters = [
        'fjord.suggest.providers.sumo.SUMOSuggest'
    ]

    def test_get_suggestions(self):
        url = reverse('feedback', args=(u'firefox',))
        desc = u'slow browser please speed improve i am wait speed improv 2'

        # Post some basic feedback that meets the SUMO Suggest
        # Provider standards and follow through to the Thank You
        # page. This triggers the suggestions and docs should be
        # in the session.
        resp = self.client.post(url, {
            'happy': 0,
            'description': desc,
        }, follow=True)

        feedback_id = self.client.session['response_id']
        session_key = SUMO_SUGGEST_SESSION_KEY.format(feedback_id)

        # Verify we get the right number of docs from the SUMO Suggest
        # API and that the urls start with SUMO_HOST.
        docs = self.client.session[session_key]
        assert 0 < len(docs) <= 3
        for doc in docs:
            assert doc['url'].startswith(SUMO_HOST)

        # Note: Since SUMO content changes, we can't check specific
        # strings since we don't really know what it's going to
        # return.

        links = resp.context['suggestions']
        assert links[0].provider == 'sumosuggest'
        assert links[0].provider_version == 1

        # Verify that the first link has non-empty summary, url and
        # description.
        assert links[0].summary
        assert links[0].url
        assert links[0].description
