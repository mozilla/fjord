#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from pages.base import Page


class ProductFilter(Page):

    class ComboFilter(Page):

        _product_checkbox_locator = (By.CSS_SELECTOR, ".bars[name='product'] input")
        _version_checkbox_locator = (By.CSS_SELECTOR, ".bars[name='version'] input")

        @property
        def products(self):
            """Returns a list of available products."""
            select = self.selenium.find_elements(*self._product_checkbox_locator)
            return [element.get_attribute('value') for element in select]

        @property
        def selected_product(self):
            """Returns the currently selected product."""
            return self.selenium.find_element(*self._product_checkbox_locator).get_attribute('value')

        def select_product(self, product):
            """Selects a product."""
            product = product.lower().replace(' ', '-')
            select = self.selenium.find_element(self._product_checkbox_locator[0],
                                                self._product_checkbox_locator[1] + "[name='%s']" % product)
            if not select.is_selected():
                select.click()

        def unselect_product(self, product):
            """Un-Selects a product."""
            product = product.lower().replace(' ', '-')
            select = self.selenium.find_element(self._product_checkbox_locator[0],
                                                self._product_checkbox_locator[1] + "[name='%s']" % product)
            if select.is_selected():
                select.click()

        @property
        def versions(self):
            """Returns a list of available versions."""
            select = self.selenium.find_elements(*self._version_checkbox_locator)
            return [element.get_attribute('value') for element in select]

        @property
        def selected_version(self):
            """Returns the currently selected product version."""
            return self.selenium.find_element(self._version_checkbox_locator[0],
                                              self._version_checkbox_locator[1]).get_attribute('value')

        def select_version(self, version):
            """Selects a product version."""
            select = self.selenium.find_element(self._version_checkbox_locator[0],
                                                self._version_checkbox_locator[1] + "[value ='%s']" % version)
            if not select.is_selected():
                select.click()

        def unselect_version(self, version):
            """Un-Selects a product version."""
            select = self.selenium.find_element(self._version_checkbox_locator[0],
                                                self._version_checkbox_locator[1] + "[value ='%s']" % version)
            if select.is_selected():
                select.click()
