#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import BasePage, Page


class ThemesPage(BasePage):

    _page_title = 'Themes :: Firefox Input'

    _themes_locator = (By.CSS_SELECTOR, '#themes li.theme')

    @property
    def themes(self):
        return [self.Theme(self.testsetup, element) for element in self.selenium.find_elements(*self._themes_locator)]

    class Theme(Page):

        _type_locator = (By.CLASS_NAME, 'type')
        _similar_messages_locator = (By.CLASS_NAME, 'more')

        def __init__(self, testsetup, element):
            Page.__init__(self, testsetup)
            self._root_element = element

        @property
        def type(self):
            return self._root_element.find_element(*self._type_locator).text

        def click_similar_messages(self):
            self._root_element.find_element(*self._similar_messages_locator).click()
            from pages.desktop.theme import ThemePage
            return ThemePage(self.testsetup)
