#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import urllib
from urlparse import urlparse

from selenium.common.exceptions import (
    ElementNotVisibleException,
    NoSuchElementException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from unittestzero import Assert


class Page(object):

    def __init__(self, testsetup):
        self.testsetup = testsetup
        self.base_url = testsetup.base_url
        self.selenium = testsetup.selenium
        self.timeout = testsetup.timeout

    @property
    def is_the_current_page(self):
        if self._page_title:
            WebDriverWait(self.selenium, self.timeout).until(lambda s: s.title)

        Assert.equal(self.selenium.title, self._page_title,
            "Expected page title: %s. Actual page title: %s" % (self._page_title, self.selenium.title))
        return True

    def is_element_visible(self, locator):
        try:
            return self.selenium.find_element(*locator).is_displayed()
        except:
            return False

    def is_element_not_visible(self, *locator):
        self.selenium.implicitly_wait(0)
        try:
            return not self.selenium.find_element(*locator).is_displayed()
        except (NoSuchElementException, ElementNotVisibleException):
            return True
        finally:
            # set back to where you once belonged
            self.selenium.implicitly_wait(self.testsetup.default_implicit_wait)

    @property
    def current_page_url(self):
        return(self.selenium.current_url)


class BasePage(Page):

    _older_messages_link_locator = (By.CSS_SELECTOR, '.pager .older')
    _newer_messages_link_locator = (By.CSS_SELECTOR, '.pager .newer')

    def scroll_to_element(self, *locator):
        """Scroll to element"""
        el = self.selenium.find_element(*locator)
        self.selenium.execute_script("window.scrollTo(0, %s)" % (el.location['y'] + el.size['height']))

    @property
    def header(self):
        from pages.desktop.regions.header import Header
        return Header(self.testsetup)

    @property
    def footer(self):
        from pages.desktop.regions.footer import Footer
        return Footer(self.testsetup)

    def click_older_messages(self):
        """Navigates to the previous page of older messages."""
        self.selenium.find_element(*self._older_messages_link_locator).click()
        WebDriverWait(self.selenium, 10).until(lambda s: self.header.is_feedback_link_visible)

    def click_newer_messages(self):
        """Navigates to the next page of newer messages."""
        self.selenium.find_element(*self._newer_messages_link_locator).click()

    @property
    def older_messages_link(self):
        return self.selenium.find_element(*self._older_messages_link_locator).text

    @property
    def newer_messages_link(self):
        return self.selenium.find_element(*self._newer_messages_link_locator).text

    @property
    def is_older_messages_link_visible(self):
        return self.is_element_visible(self._older_messages_link_locator)

    @property
    def is_newer_messages_link_visible(self):
        return self.is_element_visible(self._newer_messages_link_locator)

    @property
    def is_newer_messages_link_not_visible(self):
        return self.is_element_not_visible(self._newer_messages_link_locator)

    def _value_from_url(self, param):
        """Returns the value for the specified parameter in the URL."""
        url = urlparse(self.selenium.current_url)
        if param in url[4]:
            params = dict([part.split('=') for part in url[4].split('&')])
            return urllib.unquote(params[param])

    @property
    def feedback_type_from_url(self):
        """Returns the feedback type (praise, issues, ideas) from the current location URL."""
        return self._value_from_url("s")

    @property
    def platform_from_url(self):
        """Returns the platform from the current location URL."""
        return self._value_from_url("platform")

    @property
    def product_from_url(self):
        """Returns the product from the current location URL.

        NOTE: if the site is on the homepage (not on the search page) and default/latest
        version is selected then the URL will not contain the product parameter.

        """
        return self._value_from_url("product")

    @property
    def search_term_from_url(self):
        """Returns the search value from the current location URL."""
        return self._value_from_url("q")

    @property
    def version_from_url(self):
        """Returns the version from the current location URL.

        NOTE: if the site is on the homepage (not on the search page) and default/latest
        version is selected then the URL will not contain the version parameter.

        """
        return self._value_from_url("version")

    @property
    def date_start_from_url(self):
        """Returns the date_start value from the current location URL."""
        return self._value_from_url("date_start")

    @property
    def date_end_from_url(self):
        """Returns the date_end value from the current location URL."""
        return self._value_from_url("date_end")

    @property
    def page_from_url(self):
        """Returns the page value from the current location URL."""
        return int(self._value_from_url("page"))

    @property
    def locale_from_url(self):
        """Returns the locale value from the current location URL."""
        return self._value_from_url("locale")
