#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class PlatformFilter(Page):

    class CheckboxFilter(Page):

        _platform_checkbox_locator = (By.CSS_SELECTOR, ".bars[name='platform'] input")
        _platforms_locator = (By.CSS_SELECTOR, "ul[name='platform'] li")

        @property
        def platforms(self):
            """Returns a list of Platform instances"""
            return [self.Platform(self.testsetup, element) for element in self.selenium.find_elements(*self._platforms_locator)]

        @property
        def selected_platform(self):
            """Returns the currently selected platform."""
            for platform in self.platforms:
                if platform.is_selected:
                    return platform

        def select_platform(self, value):
            """Selects a platform."""
            select = self.selenium.find_element(
                self._platform_checkbox_locator[0],
                self._platform_checkbox_locator[1] + '[value="%s"]' % value)
            if not select.is_selected():
                select.click()

        def unselect_platform(self, value):
            select = self.selenium.find_element(
                self._platform_checkbox_locator[0],
                self._platform_checkbox_locator[1] + '[value="%s"]' % value)
            if select.is_selected():
                select.click()

        def platform(self, name):
            for platform in self.platforms:
                if platform.name == name:
                    return platform
            raise Exception('Platform not found: %s' % name)

        class Platform(Page):

            _checkbox_locator = (By.TAG_NAME, 'input')
            _name_locator = (By.CSS_SELECTOR, 'label > span:nth-child(2)')
            _message_count_locator = (By.CLASS_NAME, 'count')

            def __init__(self, testsetup, element):
                Page.__init__(self, testsetup)
                self._root_element = element

            @property
            def is_selected(self):
                return self._root_element.find_element(*self._checkbox_locator).is_selected()

            @property
            def name(self):
                return self._root_element.find_element(*self._name_locator).text

            @property
            def code(self):
                return self._root_element.find_element(*self._checkbox_locator).get_attribute('value')

            @property
            def message_count(self):
                # TODO Use native mouse interactions to hover over element to get the text
                message_count = self._root_element.find_element(*self._message_count_locator)
                return int(self.selenium.execute_script('return arguments[0].textContent', message_count))

            def click(self):
                self._root_element.find_element(*self._checkbox_locator).click()
