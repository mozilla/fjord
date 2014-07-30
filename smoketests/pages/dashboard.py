#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import urllib
from urlparse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from pages.base import Page
from pages.regions.message import Message


class DashboardPage(Page):
    _page_title = 'Welcome :: Firefox Input'

    _older_messages_link_locator = (By.CSS_SELECTOR, '.pager .older')
    _newer_messages_link_locator = (By.CSS_SELECTOR, '.pager .newer')

    _no_messages_locator = (By.ID, 'nomessages')
    _warning_heading_locator = (By.CSS_SELECTOR, '#message-warning h3')
    _search_box = (By.NAME, 'q')
    _chart_locator = (By.ID, 'feedback-chart')
    _total_message_count_locator = (By.CSS_SELECTOR, '.count > p > strong')
    _total_message_count_heading_locator = (By.CSS_SELECTOR, '#big-count h3')
    _messages_column_heading_locator = (By.CSS_SELECTOR, '#messages h2')
    _messages_locator = (By.CSS_SELECTOR, '.opinion')
    _date_start = (By.CSS_SELECTOR, 'div#whentext input[name=date_start]')
    _date_end = (By.CSS_SELECTOR, 'div#whentext input[name=date_end]')
    _date_set = (By.ID, 'whensubmit')

    def go_to_dashboard_page(self):
        self.selenium.get(self.base_url + '/')
        self.is_the_current_page

    def click_search_box(self):
        self.selenium.find_element(*self._search_box).click()

    @property
    def header(self):
        from pages.regions.header import Header
        return Header(self.testsetup)

    @property
    def footer(self):
        from pages.regions.footer import Footer
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
        return self.is_element_visible_no_wait(self._older_messages_link_locator)

    @property
    def is_newer_messages_link_visible(self):
        return self.is_element_visible_no_wait(self._newer_messages_link_locator)

    def _value_from_url(self, param):
        """Returns the value for the specified parameter in the URL."""
        url = urlparse(self.selenium.current_url)
        if param in url[4]:
            params = dict([part.split('=') for part in url[4].split('&')])
            return urllib.unquote(params[param])

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

    @property
    def locale_filter(self):
        from pages.regions.locale_filter import LocaleFilter
        return LocaleFilter(self.testsetup)

    @property
    def platform_filter(self):
        from pages.regions.platform_filter import PlatformFilter
        return PlatformFilter.CheckboxFilter(self.testsetup)

    @property
    def type_filter(self):
        from pages.regions.type_filter import TypeFilter
        return TypeFilter.CheckboxFilter(self.testsetup)

    @property
    def product_filter(self):
        from pages.regions.product_filter import ProductFilter
        return ProductFilter.ComboFilter(self.testsetup)

    @property
    def date_filter(self):
        from pages.regions.date_filter import DateFilter
        return DateFilter(self.testsetup)

    def set_date_range(self, date_start, date_end=None):
        if date_end is None:
            date_end = datetime.date.today().strftime('%Y-%m-%d')

        date_start_box = self.selenium.find_element(*self._date_start)
        date_start_box.clear()
        date_start_box.send_keys(date_start)
        date_end_box = self.selenium.find_element(*self._date_end)
        date_end_box.clear()
        date_end_box.send_keys(date_end)

        self.selenium.find_element(*self._date_set).click()

    def search_for(self, search_string):
        search_box = self.selenium.find_element(*self._search_box)
        search_box.send_keys(search_string)
        search_box.send_keys(Keys.RETURN)

    @property
    def search_box(self):
        return self.selenium.find_element(*self._search_box).get_attribute('value')

    @property
    def search_box_placeholder(self):
        return self.selenium.find_element(*self._search_box).get_attribute('placeholder')

    @property
    def message_column_heading(self):
        return self.selenium.find_element(*self._messages_column_heading_locator).text

    @property
    def total_message_count(self):
        return int(self.selenium.find_element(*self._total_message_count_locator).text.replace(',', ''))

    @property
    def total_message_count_heading(self):
        """Get the total messages header value."""
        return self.selenium.find_element(*self._total_message_count_heading_locator).text

    @property
    def messages(self):
        self.selenium.implicitly_wait(0)
        try:
            return [Message(self.testsetup, message) for message in self.selenium.find_elements(*self._messages_locator)]
        finally:
            # set back to where you once belonged
            self.selenium.implicitly_wait(self.testsetup.default_implicit_wait)

    @property
    def no_messages(self):
        return self.total_message_count == 0

    @property
    def is_chart_visible(self):
        return self.is_element_visible(self._chart_locator)

    @property
    def warning_heading(self):
        return self.selenium.find_element(*self._warning_heading_locator).text

    @property
    def no_messages_message(self):
        return self.selenium.find_element(*self._no_messages_locator).text
