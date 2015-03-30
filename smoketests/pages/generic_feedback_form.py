#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.base import Page
from pages.generic_feedback_picker import PickerPage
from pages.generic_feedback_thanks import ThanksPage


class GenericFeedbackFormPage(Page):
    _page_title = 'Submit Your Feedback :: Firefox Input'

    _intro_card_locator = (By.ID, 'intro')
    _picker_link_locator = (By.CSS_SELECTOR, '#back-to-picker a')

    _back_locator = (By.ID, 'back-button')

    _happy_button_locator = (By.ID, 'happy-button')
    _sad_button_locator = (By.ID, 'sad-button')

    _moreinfo_card_locator = (By.ID, 'moreinfo')
    _description_locator = (By.ID, 'description')
    _description_character_count_locator = (By.ID, 'description-counter')
    _url_locator = (By.ID, 'id_url')
    _email_checkbox_locator = (By.ID, 'email-ok')
    _email_locator = (By.ID, 'id_email')

    _submit_locator = (By.ID, 'form-submit-btn')

    _support_page_locator = (By.LINK_TEXT, 'Firefox Support')

    def go_to_feedback_page(self, product_name, querystring=None):
        url = self.base_url + '/feedback/' + product_name + '/'
        if querystring:
            url = url + '?' + querystring
        self.selenium.get(url)
        self.is_the_current_page

    def is_product(self, product_name):
        # Make sure we're on the intro card
        self.selenium.find_element(*self._intro_card_locator)

        # Get the first ask and make sure it has the product name in
        # it
        first_ask = self.selenium.find_element(By.CSS_SELECTOR, 'div.ask:first-child').text
        return product_name in first_ask

    def go_to_picker_page(self):
        picker_pg = PickerPage(self.testsetup)
        self.selenium.find_element(*self._picker_link_locator).click()
        WebDriverWait(self.selenium, 10).until(lambda s: picker_pg.is_the_current_page)
        return picker_pg

    def type_feedback(self, feedback):
        self.selenium.find_element(*self._feedback_locator).send_keys(feedback)

    def click_support_page(self):
        self.selenium.find_element(*self._support_page_locator).click()

    def click_happy_feedback(self):
        self.selenium.find_element(*self._happy_button_locator).click()
        self.wait_for(self._description_locator)

    def click_sad_feedback(self):
        self.selenium.find_element(*self._sad_button_locator).click()
        self.wait_for(self._description_locator)

    def click_back(self):
        self.selenium.find_element(*self._back_locator).click()
        self.wait_for(self._happy_button_locator)

    def set_description_execute_script(self, text):
        """Sets the value of the description textarea using execute_script

        :arg text: The text to set

        We use ``execute_script`` here because sending keys one at a time
        takes a crazy amount of time for texts > 200 characters.

        """
        text = text.replace("'", "\\'").replace('"', '\\"')
        self.selenium.execute_script("$('#description').val('" + text + "')")

    def set_description(self, text):
        desc = self.selenium.find_element(*self._description_locator)
        desc.clear()
        desc.send_keys(text)

    def update_description(self, text):
        desc = self.selenium.find_element(*self._description_locator)
        desc.send_keys(text)

    def set_url(self, text):
        url = self.selenium.find_element(*self._url_locator)
        url.clear()
        url.send_keys(text)

    def check_email_checkbox(self, checked=True):
        self.wait_for(self._email_checkbox_locator)
        checkbox = self.selenium.find_element(*self._email_checkbox_locator)
        if checked != checkbox.is_selected():
            checkbox.click()

    def set_email(self, text):
        if not self.is_element_visible(self._email_locator):
            self.wait_for(self._email_locator)

        email = self.selenium.find_element(*self._email_locator)
        email.clear()
        email.send_keys(text)

    @property
    def is_submit_enabled(self):
        # return not 'disabled' in self.selenium.find_element(*self._submit_feedback_locator).get_attribute('class'        
        return self.selenium.find_element(*self._submit_locator).is_enabled()

    def submit(self, expect_success=True):
        self.selenium.find_element(*self._submit_locator).click()
        if expect_success:
            return ThanksPage(self.testsetup)

    @property
    def support_page_link_address(self):
        return self.selenium.find_element(*self._support_page_locator).get_attribute('href')

    @property
    def is_url_valid(self):
        return not 'invalid' in self.selenium.find_element(*self._url_locator).get_attribute('class')

    @property
    def is_email_valid(self):
        return not 'invalid' in self.selenium.find_element(*self._email_locator).get_attribute('class')

    @property
    def remaining_character_count(self):
        return int(self.selenium.find_element(*self._description_character_count_locator).text)
