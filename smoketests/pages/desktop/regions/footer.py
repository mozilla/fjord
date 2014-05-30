#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class Footer(Page):

    _privacy_policy_link_locator = (By.CSS_SELECTOR, '#footer-links a:nth-child(1)')
    _legal_notices_link_locator = (By.CSS_SELECTOR, '#footer-links a:nth-child(2)')
    _report_trademark_abuse_link_locator = (By.CSS_SELECTOR, '#footer-links a:nth-child(3)')
    _about_input_link_locator = (By.CSS_SELECTOR, '#footer-links a:nth-child(5)')
    _unless_otherwise_noted_link_locator = (By.CSS_SELECTOR, '#copyright p:nth-child(3) a:nth-child(1)')
    _creative_commons_link_locator = (By.CSS_SELECTOR, '#copyright p:nth-child(3) a:nth-child(3)')
    _language_dropdown_locator = (By.ID, 'language')

    @property
    def is_language_dropdown_visible(self):
        return self.is_element_visible(self._language_dropdown_locator)

    @property
    def privacy_policy(self):
        return self.selenium.find_element(*self._privacy_policy_link_locator).text

    @property
    def legal_notices(self):
        return self.selenium.find_element(*self._legal_notices_link_locator).text

    @property
    def report_trademark_abuse(self):
        return self.selenium.find_element(*self._report_trademark_abuse_link_locator).text

    @property
    def unless_otherwise_noted(self):
        return self.selenium.find_element(*self._unless_otherwise_noted_link_locator).text

    @property
    def creative_commons(self):
        return self.selenium.find_element(*self._creative_commons_link_locator).text

    @property
    def about_input(self):
        return self.selenium.find_element(*self._about_input_link_locator).text
