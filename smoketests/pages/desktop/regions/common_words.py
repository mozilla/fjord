#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class CommonWordsRegion(Page):

    _header_locator = (By.XPATH, "id('filter_themes')/h3/a/text()[1]")
    _common_words_locator = (By.CSS_SELECTOR, 'filter_themes li')

    @property
    def common_words_header(self):
        return self.selenium.find_element(*self._header_locator)

    def common_words(self):
        return [self.CommonWord(self.testsetup, element) for element in self.selenium.find_elements(*self._common_words_locator)]

    class CommonWord(Page):

        _name_locator = (By.CSS_SELECTOR, 'a > strong')
        _message_count_locator = (By.CLASS_NAME, 'count')

        def __init__(self, testsetup, element):
            Page.__init__(self, testsetup)
            self._root_element = element

        @property
        def name(self):
            return self._root_element.find_element(*self._name_locator).text

        @property
        def message_count(self):
            return self._root_element.find_element(*self._message_count_locator).text

        def select(self):
            self._root_element.find_element(*self._name_locator).click()
