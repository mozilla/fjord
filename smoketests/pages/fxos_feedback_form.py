#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.feedback import FeedbackPage


class FxOSFeedbackFormPage(FeedbackPage):
    _page_title = 'Submit Your Feedback :: Firefox Input'

    def go_to_feedback_page(self):
        self.selenium.get(self.base_url + '/feedback/fxos/')
        self.is_the_current_page

    # Intro card
    _happy_button_locator = (By.CSS_SELECTOR, '#intro #happy-button')
    _sad_button_locator = (By.CSS_SELECTOR, '#intro #sad-button')

    def click_happy_feedback(self):
        self.selenium.find_element(*self._happy_button_locator).click()
        self.wait_for(self._country_select_locator)

    def click_sad_feedback(self):
        self.selenium.find_element(*self._sad_button_locator).click()
        self.wait_for(self._country_select_locator)

    # Country selection card
    _country_select_locator = (By.CSS_SELECTOR, '#country select')
    _country_next_locator = (By.CSS_SELECTOR, '#country button.next')

    def click_country_next(self):
        self.selenium.find_element(*self._country_next_locator).click()
        self.wait_for(self._device_select_locator)

    # Device selection card
    _device_select_locator = (By.CSS_SELECTOR, '#device select')
    _device_next_locator = (By.CSS_SELECTOR, '#device button.next')

    def click_device_next(self):
        self.selenium.find_element(*self._device_next_locator).click()
        self.wait_for(self._moreinfo_text_locator)

    # Moreinfo card
    _moreinfo_text_locator = (By.CSS_SELECTOR, '#moreinfo #description')
    _url_locator = (By.ID, 'id_url')
    _email_checkbox_locator = (By.CSS_SELECTOR, '#moreinfo input#email-ok')
    _email_text_locator = (By.CSS_SELECTOR, '#moreinfo input#id_email')
    _submit_locator = (By.CSS_SELECTOR, '#moreinfo button.submit')

    def set_description_execute_script(self, text):
        """Sets the value of the description textarea using execute_script

        :arg text: The text to set

        We use ``execute_script`` here because sending keys one at a time
        takes a crazy amount of time for texts > 200 characters.

        """
        text = text.replace("'", "\\'").replace('"', '\\"')
        self.selenium.execute_script("$('#description').val('" + text + "')")

    def set_description(self, text):
        desc = self.selenium.find_element(*self._moreinfo_text_locator)
        desc.clear()
        desc.send_keys(text)

    def update_description(self, text):
        desc = self.selenium.find_element(*self._moreinfo_text_locator)
        desc.send_keys(text)

    @property
    def is_submit_enabled(self):
        return self.selenium.find_element(*self._submit_locator).is_enabled()

    def set_url(self, text):
        url = self.selenium.find_element(*self._url_locator)
        url.clear()
        url.send_keys(text)

    def check_email_checkbox(self, checked=True):
        if not self.is_element_visible(self._email_checkbox_locator):
            self.wait_for(self._email_checkbox_locator)

        checkbox = self.selenium.find_element(*self._email_checkbox_locator)
        if checked != checkbox.is_selected():
            checkbox.click()

    def set_email(self, text):
        if not self.is_element_visible(self._email_text_locator):
            self.wait_for(self._email_text_locator)

        email = self.selenium.find_element(*self._email_text_locator)
        email.clear()
        email.send_keys(text)

    _thanks_locator = (By.CSS_SELECTOR, '#thanks')

    def submit(self, expect_success=True):
        self.selenium.find_element(*self._submit_locator).click()
        if expect_success:
            self.wait_for((By.CSS_SELECTOR, '#thanks'))

    @property
    def current_card(self):
        for card in ('intro', 'country', 'device', 'moreinfo', 'email',
                     'submitting', 'thanks', 'failure', 'tryagain'):

            if self.is_element_visible_no_wait((By.CSS_SELECTOR, '#' + card)):
                return card
