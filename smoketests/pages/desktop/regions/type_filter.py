#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class TypeFilter(Page):

    class ButtonFilter(Page):

        _selected_type_locator = (By.CSS_SELECTOR, '#filter_type a.selected')
        _all_locator = (By.CSS_SELECTOR, '#filter_type li:nth-child(1) a')
        _praise_locator = (By.CSS_SELECTOR, '#filter_type li:nth-child(2) a')
        _issues_locator = (By.CSS_SELECTOR, '#filter_type li:nth-child(3) a')
        _ideas_locator = (By.CSS_SELECTOR, '#filter_type li:nth-child(4) a')

        @property
        def selected_type(self):
            return self.selenium.find_element(*self._selected_type_locator).text

        def click_issues(self):
            self.selenium.find_element(*self._issues_locator).click()


    class CheckboxFilter(Page):

        _types_locator = (By.CSS_SELECTOR, '#filter_type li')

        @property
        def types(self):
            return [self.Type(self.testsetup, element) for element in self.selenium.find_elements(*self._types_locator)]

        class Type(Page):

            _checkbox_locator = (By.TAG_NAME, 'input')
            _name_locator = (By.CSS_SELECTOR, 'label > strong')
            _message_count_locator = (By.CLASS_NAME, 'count')
            _percent_locator = (By.CLASS_NAME, 'perc')

            def __init__(self, testsetup, element):
                Page.__init__(self, testsetup)
                self._root_element = element

            @property
            def is_selected(self):
                return self._root_element.find_element(*self._checkbox_locator).is_checked()

            @property
            def name(self):
                return self._root_element.find_element(*self._name_locator).text

            @property
            def message_count(self):
                return self._root_element.find_element(*self._message_count_locator).text

            @property
            def percent(self):
                return self._root_element.find_element(*self._percent_locator).text

            def select(self):
                return self._root_element.find_element(*self._checkbox_locator).click
