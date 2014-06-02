#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class Message(Page):

    _type_locator = (By.CSS_SELECTOR, 'span.sprite')
    _body_locator = (By.CSS_SELECTOR, 'p')
    _platform_locator = (By.CSS_SELECTOR, '.meta li:nth-child(3) a')
    _locale_locator = (By.CSS_SELECTOR, '.meta li:nth-child(4) a')
    _site_locator = (By.CSS_SELECTOR, '.meta li:nth-child(5)')
    _permalink_locator = (By.CSS_SELECTOR, '.meta li:nth-child(5) a')

    def __init__(self, testsetup, element):
        Page.__init__(self, testsetup)
        self._root_element = element

    def click_locale(self):
        self._root_element.find_element(*self._locale_locator).click()

    def click_timestamp(self):
        self._root_element.find_element(*self._time_locator).click()

    @property
    def is_locale_visible(self):
        return self.is_element_visible(self._locale_locator)

    @property
    def type(self):
        return self._root_element.find_element(*self._type_locator).text

    @property
    def body(self):
        return self._root_element.find_element(*self._body_locator).text

    @property
    def locale(self):
        return self._root_element.find_element(*self._locale_locator).text

    @property
    def site(self):
        return self._root_element.find_element(*self._site_locator).text

    @property
    def response_id(self):
        permalink = self._root_element.find_element(*self._permalink_locator)
        link = permalink.get_attribute('href')
        return link.split('/')[-1]
