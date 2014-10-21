#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.base import Page


class Product(Page):
    _name_locator = (By.CSS_SELECTOR, 'h3')

    def __init__(self, testsetup, element):
        Page.__init__(self, testsetup)
        self._root_element = element

    @property
    def name(self):
        return self._root_element.find_element(*self._name_locator).text

    def click(self):
        # FIXME: Import here to avoid circular import
        from pages.generic_feedback_form_dev import GenericFeedbackFormDevPage

        # Clicks on the product which goes to the feedback page.
        feedback_pg = GenericFeedbackFormDevPage(self.testsetup)
        self._root_element.click()
        WebDriverWait(self.selenium, 10).until(lambda s: feedback_pg.is_the_current_page)
        return feedback_pg


class PickerPage(Page):
    _page_title = 'Which product? :: Firefox Input'

    _products_locator = (By.CSS_SELECTOR, '.product-card')

    def go_to_picker_page(self):
        self.selenium.get(self.base_url + '/feedback/?feedbackdev=1')
        self.is_the_current_page

    @property
    def products(self):
        self.selenium.implicitly_wait(0)
        try:
            return [Product(self.testsetup, product)
                    for product in self.selenium.find_elements(*self._products_locator)]
        finally:
            # set back to where you once belonged
            self.selenium.implicitly_wait(self.testsetup.default_implicit_wait)
