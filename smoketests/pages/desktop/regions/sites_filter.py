#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class SitesFilter(Page):

    _header_locator = (By.XPATH, "id('filter_sites')/h3/a/text()[1]")
    _sites_locator = (By.CSS_SELECTOR, '#filter_sites li')

    @property
    def header(self):
        return self.selenium.find_element(*self._header_locator).text

    @property
    def sites(self):
        return [self.Site(self.testsetup, element) for element in self.selenium.find_elements(*self._sites_locator)]

    class Site(Page):

        _site_locator = (By.CSS_SELECTOR, 'a > strong')

        def __init__(self, testsetup, element):
            Page.__init__(self, testsetup)
            self._root_element = element

        @property
        def url(self):
            return self._root_element.find_element(*self._site_locator).text

        def click(self):
            return self._root_element.find_element(*self._site_locator).click
