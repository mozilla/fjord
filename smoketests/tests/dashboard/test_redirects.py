# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import requests


FIREFOX_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.5; rv:5.0) Gecko/20100101 Firefox/5.0'
SAFARI_UA = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27'


class RedirectsBase(object):
    def _check_redirect(self, testsetup, url, expected_url, user_agent=FIREFOX_UA, locale='en-US'):
        url = testsetup.base_url + url
        expected_url = testsetup.base_url + expected_url
        if testsetup.selenium:
            testsetup.selenium.get(url)
            assert testsetup.selenium.current_url == expected_url
        else:
            headers = {
                'user-agent': user_agent,
                'accept-language': locale
            }
            r = requests.get(url, headers=headers)
            assert r.url == expected_url


class TestDashboardRedirects(RedirectsBase):
    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_root_without_locale_redirects_to_root_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/', '/en-US/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_root_without_locale_redirects_to_root_with_german_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/', '/de/', locale='de')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_feedback_search_without_locale_redirects_to_feedback_search_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/?sentiment=happy', '/en-US/?sentiment=happy')


class TestFeedbackRedirects(RedirectsBase):
    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_feedback_without_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/feedback', '/en-US/feedback')
        self._check_redirect(mozwebqa, '/feedback/', '/en-US/feedback/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_happy_backwards_compatibility(self, mozwebqa):
        self._check_redirect(mozwebqa, '/happy', '/en-US/feedback?happy=1')
        self._check_redirect(mozwebqa, '/happy/', '/en-US/feedback?happy=1')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_sad_backwards_compatibility(self, mozwebqa):
        self._check_redirect(mozwebqa, '/sad', '/en-US/feedback?happy=0')
        self._check_redirect(mozwebqa, '/sad/', '/en-US/feedback?happy=0')
