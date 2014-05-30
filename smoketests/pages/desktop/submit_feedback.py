#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.base import BasePage


class SubmitFeedbackPage(BasePage):

    _page_title = 'Submit Your Feedback :: Firefox Input'

    _idea_page_locator = (By.ID, 'idea')
    _happy_page_locator = (By.ID, 'happy')
    _sad_page_locator = (By.ID, 'sad')
    _intro_page_locator = (By.ID, 'intro')

    _idea_button_locator = (By.ID, 'intro-idea')
    _happy_button_locator = (By.ID, 'intro-happy')
    _sad_button_locator = (By.ID, 'intro-sad')

    _support_page_locator = (By.LINK_TEXT, 'Firefox Support')

    def go_to_submit_feedback_page(self):
        self.selenium.get(self.base_url + '/feedback/')
        self.is_the_current_page

    def type_feedback(self, feedback):
        self.selenium.find_element(*self._feedback_locator).send_keys(feedback)

    def click_support_page(self):
        self.selenium.find_element(*self._support_page_locator).click()

    def wait_for_page_to_slide_into_view(self, page_locator):
        WebDriverWait(self.selenium, self.timeout).until(lambda s: self.is_element_visible(page_locator))
        WebDriverWait(self.selenium, self.timeout).until(lambda s: 'entering' not in s.find_element(*page_locator).get_attribute('class'))

    def click_happy_feedback(self):
        self.selenium.find_element(*self._happy_button_locator).click()
        self.wait_for_page_to_slide_into_view(self._happy_page_locator)
        from pages.desktop.submit_happy_feedback import SubmitHappyFeedbackPage
        return SubmitHappyFeedbackPage(self.testsetup)

    def click_sad_feedback(self):
        self.selenium.find_element(*self._sad_button_locator).click()
        self.wait_for_page_to_slide_into_view(self._sad_page_locator)
        from pages.desktop.submit_sad_feedback import SubmitSadFeedbackPage
        return SubmitSadFeedbackPage(self.testsetup)

    def click_idea_feedback(self):
        self.selenium.find_element(*self._idea_button_locator).click()
        self.wait_for_page_to_slide_into_view(self._idea_page_locator)
        from pages.desktop.submit_idea import SubmitIdeaPage
        return SubmitIdeaPage(self.testsetup)

    def click_back(self):
        self.selenium.find_element(*self._back_locator).click()
        self.wait_for_page_to_slide_into_view(self._intro_page_locator)

    @property
    def support_page_link_address(self):
        return self.selenium.find_element(*self._support_page_locator).get_attribute('href')

    @property
    def error_message(self):
        return self.selenium.find_element(*self._error_locator).text

    @property
    def remaining_character_count(self):
        return int(self.selenium.find_element(*self._remaining_character_count_locator).text)

    @property
    def is_remaining_character_count_limited(self):
        css_class = self.selenium.find_element(*self._remaining_character_count_locator).get_attribute('class')
        return 'limited-characters-remaining' in css_class and not 'no-characters-remaining' in css_class

    @property
    def is_remaining_character_count_negative(self):
        return 'no-characters-remaining' in self.selenium.find_element(*self._remaining_character_count_locator).get_attribute('class')

    @property
    def is_submit_feedback_enabled(self):
        return not 'disabled' in self.selenium.find_element(*self._submit_feedback_locator).get_attribute('class')

    def submit_feedback(self, expected_result='success'):
        self.selenium.find_element(*self._submit_feedback_locator).click()
        if expected_result == 'success':
            from pages.desktop.thanks import ThanksPage
            return ThanksPage(self.testsetup)
