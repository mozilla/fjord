#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class FeedbackPage(Page):
    _privacy_locator = (By.CSS_SELECTOR, 'footer #privacy-policy')

    @property
    def has_privacy_link(self):
        href = self.selenium.find_element(*self._privacy_locator).get_attribute('href')
        return href == 'http://www.mozilla.org/privacy/websites'
