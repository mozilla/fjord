#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import BasePage
from pages.desktop.regions.message import Message


class ThemePage(BasePage):

    _messages_heading_locator = (By.CSS_SELECTOR, '#messages h2')
    _theme_callout_locator = (By.ID, 'theme-callout')
    _back_link_locator = (By.CSS_SELECTOR, 'a.exit')
    _messages_locator = (By.CSS_SELECTOR, '#messages .message')
    _total_message_count_locator = (By.CSS_SELECTOR, '#big-count p')
    _previous_page_link_locator = (By.CSS_SELECTOR, '.pager .prev')
    _next_page_link_locator = (By.CSS_SELECTOR, '.pager .next')

    def click_previous_page(self):
        """Navigates to the previous page."""
        self.selenium.find_element(*self._previous_page_link_locator).click()

    def click_next_page(self):
        """Navigates to the next page."""
        self.selenium.find_element(*self._next_page_link_locator).click()

    @property
    def is_back_link_visible(self):
        """Returns true if the "Back to all themes" link is visible."""
        return self.is_element_visible(self._back_link_locator)

    @property
    def is_message_count_visible(self):
        """Returns True if the message count is visible."""
        return self.is_element_visible(self._total_message_count_locator)

    @property
    def messages_heading(self):
        """Returns the heading text of the Theme page."""
        return self.selenium.find_element(*self._messages_heading_locator).text

    @property
    def locale_filter(self):
        from pages.desktop.regions.locale_filter import LocaleFilter
        return LocaleFilter(self.testsetup)

    @property
    def platform_filter(self):
        from pages.desktop.regions.platform_filter import PlatformFilter
        return PlatformFilter.CheckboxFilter(self.testsetup)

    @property
    def theme_callout(self):
        """Returns the text value of the theme callout."""
        return self.selenium.find_element(*self._theme_callout_locator).text

    @property
    def back_link(self):
        """Returns the text value of the back link."""
        return self.selenium.find_element(*self._back_link_locator).text

    @property
    def messages(self):
        return [Message(self.testsetup, element) for element in self.selenium.find_elements(*self._messages_locator)]
