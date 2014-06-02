#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import BasePage, Page


class SitesPage(BasePage):

    _page_title = 'Sites :: Firefox Input'

    _sites_locator = (By.CSS_SELECTOR, '#themes li.site')

    def go_to_sites_page(self):
        self.selenium.get(self.base_url + '/sites/')
        self.is_the_current_page

    @property
    def product_filter(self):
        from pages.desktop.regions.product_filter import ProductFilter
        return ProductFilter.ComboFilter(self.testsetup)

    @property
    def sites(self):
        return [self.Site(self.testsetup, element) for element in self.selenium.find_elements(*self._sites_locator)]

    class Site(Page):

        _name_locator = (By.CSS_SELECTOR, '.name a')

        def __init__(self, testsetup, element):
            Page.__init__(self, testsetup)
            self._root_element = element

        @property
        def name(self):
            return self._root_element.find_element(*self._name_locator).text

        def click_name(self):
            self._root_element.find_element(*self._name_locator).click()
            from pages.desktop.themes import ThemesPage
            return ThemesPage(self.testsetup)
