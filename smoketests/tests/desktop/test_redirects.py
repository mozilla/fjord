#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittestzero import Assert
import pytest
import requests


class TestRedirects:

    _user_agent_firefox = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.5; rv:5.0) Gecko/20100101 Firefox/5.0'
    _user_agent_safari = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27'

    def _check_redirect(self, testsetup, start_url, end_url, user_agent=_user_agent_firefox, locale='en-US'):
        start_url = testsetup.base_url + start_url
        end_url = testsetup.base_url + end_url
        if testsetup.selenium:
            testsetup.selenium.get(start_url)
            Assert.equal(testsetup.selenium.current_url, end_url)
        else:
            headers = {'user-agent': user_agent,
                       'accept-language': locale}
            r = requests.get(start_url, headers=headers)
            Assert.equal(r.url, end_url)

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_root_without_locale_redirects_to_root_with_german_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/', '/de/', locale='de')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_root_without_locale_redirects_to_root_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/', '/en-US/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_without_locale_redirects_to_root_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/beta/', '/en-US/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_with_locale_redirects_to_root_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/beta/', '/en-US/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_without_locale_redirects_to_root_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/release/', '/en-US/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_with_locale_redirects_to_root_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/release/', '/en-US/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_feedback_search_without_locale_redirects_to_feedback_search_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/?sentiment=happy', '/en-US/?sentiment=happy')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_feedback_search_without_locale_redirects_to_feedback_search_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/beta/?sentiment=sad', '/en-US/?sentiment=sad')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_feedback_search_with_locale_redirects_to_feedback_search_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/beta/?sentiment=idea', '/en-US/?sentiment=idea')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_feedback_search_without_locale_redirects_to_feedback_search_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/release/?sentiment=happy', '/en-US/?sentiment=happy')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_feedback_search_with_locale_redirects_to_feedback_search_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/release/?sentiment=sad', '/en-US/?sentiment=sad')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_themes_without_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/themes/', '/en-US/themes/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_themes_without_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/beta/themes/', '/en-US/themes/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_themes_with_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/beta/themes/', '/en-US/themes/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_themes_without_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/release/themes/', '/en-US/themes/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_themes_with_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/release/themes/', '/en-US/themes/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_sites_without_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/sites/', '/en-US/sites/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_sites_without_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/beta/sites/', '/en-US/sites/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_sites_with_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/beta/sites/', '/en-US/sites/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_sites_without_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/release/sites/', '/en-US/sites/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_sites_with_locale_redirects_to_themes_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/release/sites/', '/en-US/sites/')

    @pytest.mark.nondestructive
    def test_idea_without_locale_redirects_to_idea_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/idea/', '/en-US/feedback#idea')

    @pytest.mark.nondestructive
    def test_beta_idea_without_locale_redirects_to_idea_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/beta/idea/', '/en-US/feedback#idea')

    @pytest.mark.nondestructive
    def test_beta_idea_with_locale_redirects_to_idea_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/beta/idea/', '/en-US/feedback#idea')

    @pytest.mark.nondestructive
    def test_release_idea_without_locale_redirects_to_idea_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/release/idea/', '/en-US/feedback#idea')

    @pytest.mark.nondestructive
    def test_release_idea_with_locale_redirects_to_idea_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/release/idea/', '/en-US/feedback#idea')

    @pytest.mark.nondestructive
    def test_happy_without_locale_redirects_to_happy_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/happy/', '/en-US/feedback#happy')

    @pytest.mark.nondestructive
    def test_beta_happy_without_locale_redirects_to_happy_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/beta/happy/', '/en-US/feedback#happy')

    @pytest.mark.nondestructive
    def test_beta_happy_with_locale_redirects_to_happy_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/beta/happy/', '/en-US/feedback#happy')

    @pytest.mark.nondestructive
    def test_release_happy_without_locale_redirects_to_happy_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/release/happy/', '/en-US/feedback#happy')

    @pytest.mark.nondestructive
    def test_release_happy_with_locale_redirects_to_happy_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/release/happy/', '/en-US/feedback#happy')

    @pytest.mark.nondestructive
    def test_sad_without_locale_redirects_to_sad_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/sad/', '/en-US/feedback#sad')

    @pytest.mark.nondestructive
    def test_beta_sad_without_locale_redirects_to_sad_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/beta/sad/', '/en-US/feedback#sad')

    @pytest.mark.nondestructive
    def test_beta_sad_with_locale_redirects_to_sad_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/beta/sad/', '/en-US/feedback#sad')

    @pytest.mark.nondestructive
    def test_release_sad_without_locale_redirects_to_sad_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/release/sad/', '/en-US/feedback#sad')

    @pytest.mark.nondestructive
    def test_release_sad_with_locale_redirects_to_sad_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/release/sad/', '/en-US/feedback#sad')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_feedback_without_locale_redirects_to_feedback_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/feedback/', '/en-US/feedback/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_feedback_without_locale_redirects_to_feedback_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/beta/feedback/', '/en-US/feedback/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_beta_feedback_with_locale_redirects_to_feedback_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/beta/feedback/', '/en-US/feedback/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_feedback_without_locale_redirects_to_feedback_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/release/feedback/', '/en-US/feedback/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_release_feedback_with_locale_redirects_to_feedback_with_locale(self, mozwebqa):
        self._check_redirect(mozwebqa, '/en-US/release/feedback/', '/en-US/feedback/')

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_sad_redirects_to_download_when_not_using_firefox(self, mozwebqa):
        self._check_redirect(mozwebqa, '/sad/', '/en-US/download', user_agent=self._user_agent_safari)

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_happy_redirects_to_download_when_not_using_firefox(self, mozwebqa):
        self._check_redirect(mozwebqa, '/happy/', '/en-US/download', user_agent=self._user_agent_safari)

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_idea_redirects_to_download_when_not_using_firefox(self, mozwebqa):
        self._check_redirect(mozwebqa, '/idea/', '/en-US/download', user_agent=self._user_agent_safari)

    @pytest.mark.skip_selenium
    @pytest.mark.nondestructive
    def test_feedback_redirects_to_download_when_not_using_firefox(self, mozwebqa):
        self._check_redirect(mozwebqa, '/feedback/', '/en-US/download', user_agent=self._user_agent_safari)
