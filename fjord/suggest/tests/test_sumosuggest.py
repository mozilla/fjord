import os

from mock import MagicMock, patch
from nose.tools import eq_, ok_
import requests_mock

from fjord.base.tests import TestCase, skip_if
from fjord.feedback.tests import ResponseFactory
from fjord.suggest.providers.sumosuggest import (
    SUMO_SUGGEST_API_URL,
    SUMOSuggestProvider
)


class SUMOSuggestProviderTestCase(TestCase):
    provider = SUMOSuggestProvider()

    def test_not_sad(self):
        resp = ResponseFactory(
            happy=True,  # Happy
            locale=u'en-US',
            product=u'Firefox',
            description=u'Firefox does not make good sandwiches. Srsly.'
        )
        links = self.provider.get_suggestions(resp)
        eq_(len(links), 0)

    def test_not_en_us(self):
        resp = ResponseFactory(
            happy=False,
            locale=u'fr',
            product=u'Firefox',
            description=u'Firefox does not make good sandwiches. Srsly.'
        )
        links = self.provider.get_suggestions(resp)
        eq_(len(links), 0)

    def test_not_firefox(self):
        resp = ResponseFactory(
            happy=False,
            locale=u'en-US',
            product=u'Firefox for Android',
            description=u'Firefox does not make good sandwiches. Srsly.'
        )
        links = self.provider.get_suggestions(resp)
        eq_(len(links), 0)

    def test_too_short(self):
        resp = ResponseFactory(
            happy=False,
            locale=u'en-US',
            product=u'Firefox',
            description=u'Firefox is bad.'
        )
        links = self.provider.get_suggestions(resp)
        eq_(len(links), 0)

    def test_suggestions(self):
        ret = {
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
            m.get(SUMO_SUGGEST_API_URL, json=ret)

            resp = ResponseFactory(
                happy=False,
                locale=u'en-US',
                product=u'Firefox',
                description=(
                    u'slow browser please speed improve i am wait speed improv'
                )
            )

            links = self.provider.get_suggestions(resp)
            eq_(len(links), 3)

            # Abuse the fact that we know what order the links are in
            # since we're mocking.
            for i in range(3):
                eq_(links[i].type_, 'sumosuggest')
                eq_(links[i].url, ret['documents'][i]['url'])
                eq_(links[i].summary, ret['documents'][i]['title'])
                eq_(links[i].description, ret['documents'][i]['summary'])

    def test_not_json(self):
        # If we get back text and not JSON, then the sumo search
        # suggest provider should return no links. This tests the "if
        # any exception happens, return nothing" handling.
        with requests_mock.Mocker() as m:
            m.get(SUMO_SUGGEST_API_URL, text='Gah! Something bad happened')

            patch_point = 'fjord.suggest.providers.sumosuggest.logger'
            with patch(patch_point) as logger_patch:
                # Create a mock that we can call .exception() on and
                # it makes sure it got called.
                logger_patch.exception = MagicMock()

                resp = ResponseFactory(
                    happy=False,
                    locale=u'en-US',
                    product=u'Firefox',
                    description=(
                        u'slow browser please speed improve i am wait '
                        u'speed improv'
                    )
                )

                links = self.provider.get_suggestions(resp)

                # Make sure we get back no links.
                eq_(len(links), 0)

                # Make sure logger.exception() got called once.
                eq_(logger_patch.exception.call_count, 1)


@skip_if(lambda: 'LIVE_API' not in os.environ)
class LiveSUMOSuggestProviderTestCase(TestCase):
    """This only executes if LIVE_API is defined in the environment. Otherwise
    we skip it.

    This makes it easier to test against the actual SUMO which speeds
    up development and will help us debug issues in the future.

    """
    provider = SUMOSuggestProvider()

    def test_get_suggestions(self):
        resp = ResponseFactory(
            happy=False,
            locale=u'en-US',
            product=u'Firefox',
            description=(
                u'slow browser please speed improve i am wait speed improve'
            )
        )
        links = self.provider.get_suggestions(resp)

        # Verify we get the right number of links.
        ok_(0 < len(links) <= 3)

        eq_(links[0].type_, u'sumosuggest')

        # Verify that the first link has non-empty summary, url and
        # description.
        ok_(links[0].summary)
        ok_(links[0].url)
        ok_(links[0].description)

        # Note: Since SUMO content changes, we can't check specific
        # strings since we don't really know what it's going to
        # return.
