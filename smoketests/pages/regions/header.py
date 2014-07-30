#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class Header(Page):
    _feedback_link_locator = (By.CSS_SELECTOR, 'a.dashboard')
    _main_heading_link_locator = (By.CSS_SELECTOR, 'h1 > a')

    def click_feedback_link(self):
        self.selenium.find_element(*self._feedback_link_locator).click()
        from pages.desktop.dashboard import DashboardPage
        return DashboardPage(self.testsetup)

    def click_main_heading_link(self):
        self.selenium.find_element(*self._main_heading_link_locator).click()
        from pages.desktop.dashboard import DashboardPage
        return DashboardPage(self.testsetup)

    @property
    def is_feedback_link_visible(self):
        return self.is_element_visible(self._feedback_link_locator)

    @property
    def is_main_heading_link_visible(self):
        return self.is_element_visible(self._main_heading_link_locator)
