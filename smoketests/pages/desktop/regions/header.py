#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class Header(Page):

    _feedback_link_locator = (By.CSS_SELECTOR, 'a.dashboard')
    _themes_link_locator = (By.CSS_SELECTOR, 'a.themes')
    _main_heading_link_locator = (By.CSS_SELECTOR, 'h1 > a')
    _sites_link_locator = (By.CSS_SELECTOR, 'a.issues')

    def click_feedback_link(self):
        self.selenium.find_element(*self._feedback_link_locator).click()
        from pages.desktop.feedback import FeedbackPage
        return FeedbackPage(self.testsetup)

    def click_themes_link(self):
        self.selenium.find_element(*self._themes_link_locator).click()
        from pages.desktop.themes import ThemesPage
        return ThemesPage(self.testsetup)

    def click_main_heading_link(self):
        self.selenium.find_element(*self._main_heading_link_locator).click()
        from pages.desktop.feedback import FeedbackPage
        return FeedbackPage(self.testsetup)

    def click_sites_link(self):
        self.selenium.find_element(*self._sites_link_locator).click()
        from pages.desktop.sites import SitesPage
        return SitesPage(self.testsetup)

    @property
    def is_feedback_link_visible(self):
        return self.is_element_visible(self._feedback_link_locator)

    @property
    def is_themes_link_visible(self):
        return self.is_element_visible(self._themes_link_locator)

    @property
    def is_main_heading_link_visible(self):
        return self.is_element_visible(self._main_heading_link_locator)

    @property
    def is_sites_link_visible(self):
        return self.is_element_visible(self._sites_link_locator)
