#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from pages.base import Page


class DateFilter(Page):

    _current_when_link_locator = (By.CSS_SELECTOR, 'a.when.selected')

    _last_day_locator = (By.LINK_TEXT, '1d')
    _last_seven_days_locator = (By.LINK_TEXT, '7d')
    _last_thirty_days_locator = (By.LINK_TEXT, '30d')
    _show_custom_dates_locator = (By.CSS_SELECTOR, 'a.expander')
    _custom_dates_locator = (By.CSS_SELECTOR, 'div.filter a.custom-date')
    _custom_start_date_locator = (By.CSS_SELECTOR, 'input[name=date_start]')
    _custom_end_date_locator = (By.CSS_SELECTOR, 'input[name=date_end]')

    _set_custom_date_locator = (By.ID, 'whensubmit')

    _datepicker_locator = (By.ID, 'ui-datepicker-div')
    _datepicker_calendar_locator = (By.CSS_SELECTOR, '.ui-datepicker-calendar')
    _datepicker_month_locator = (By.CSS_SELECTOR, '.ui-datepicker-month')
    _datepicker_year_locator = (By.CSS_SELECTOR, '.ui-datepicker-year')
    _datepicker_previous_month_locator = (By.CSS_SELECTOR, '.ui-datepicker-prev')
    _datepicker_next_month_locator = (By.CSS_SELECTOR, '.ui-datepicker-next')
    _datepicker_next_month_disabled_locator = (By.CSS_SELECTOR, '.ui-datepicker-next.ui-state-disabled')

    _custom_date_only_error_locator = (By.XPATH, "//div[@id='custom-date']/ul/li")
    _custom_date_first_error_locator = (By.XPATH, "//div[@id='custom-date']/ul[1]/li")
    _custom_date_second_error_locator = (By.XPATH, "//div[@id='custom-date']/ul[2]/li")

    @property
    def current_days(self):
        """Returns the link text of the currently applied days filter."""
        return self.selenium.find_element(*self._current_when_link_locator).text

    def click_last_day(self):
        return self.selenium.find_element(*self._last_day_locator).click()

    def click_last_seven_days(self):
        return self.selenium.find_element(*self._last_seven_days_locator).click()

    def click_last_thirty_days(self):
        return self.selenium.find_element(*self._last_thirty_days_locator).click()

    def enable_custom_dates(self):
        """Clicks the custom date filter button and waits for the form to appear."""
        custom_dates = self.selenium.find_element(*self._show_custom_dates_locator)
        if 'selected' not in custom_dates.get_attribute('class'):
            custom_dates.click()

    @property
    def is_custom_date_filter_visible(self):
        """Returns True if the custom date filter form is visible."""
        return self.is_element_visible(self._custom_dates_locator)

    @property
    def is_datepicker_visible(self):
        """Returns True if the datepicker pop up is visible."""
        datepicker = self.selenium.find_element(*self._datepicker_locator)
        return datepicker.is_displayed() and datepicker.location['x'] > 0

    @property
    def is_custom_start_date_visible(self):
        """Returns True if the custom start date input form is visible."""
        return self.is_element_visible(self._custom_start_date_locator)

    @property
    def is_custom_end_date_visible(self):
        """Returns True if the custom end date input form is visible."""
        return self.is_element_visible(self._custom_end_date_locator)

    @property
    def is_datepicker_next_month_button_disabled(self):
        return self.is_element_visible(self._datepicker_next_month_disabled_locator)

    def wait_for_datepicker_to_open(self):
        WebDriverWait(self.selenium, self.timeout).until(lambda s: self.is_datepicker_visible)
        WebDriverWait(self.selenium, self.timeout).until(lambda s: s.find_element(*self._datepicker_locator).size['width'] == 251)

    def wait_for_datepicker_to_close(self):
        WebDriverWait(self.selenium, self.timeout).until(lambda s: not self.is_datepicker_visible)

    def close_datepicker(self):
        self.selenium.find_element(*self._custom_start_date_locator).send_keys(Keys.ESCAPE)
        WebDriverWait(self.selenium, self.timeout).until(lambda s: not self.is_datepicker_visible)

    def click_start_date(self):
        """Clicks the start date in the custom date filter form and waits for the datepicker to appear."""
        self.selenium.find_element(*self._custom_start_date_locator).click()
        self.wait_for_datepicker_to_open()

    def click_end_date(self):
        """Clicks the end date in the custom date filter form and waits for the datepicker to appear."""
        self.selenium.find_element(*self._custom_end_date_locator).click()
        self.wait_for_datepicker_to_open()

    def click_previous_month(self):
        """Clicks the previous month button in the datepicker."""
        self.selenium.find_element(*self._datepicker_previous_month_locator).click()

    def click_next_month(self):
        """Clicks the next month button in the datepicker."""
        # TODO: Throw an error if the next month button is disabled
        self.selenium.find_element(*self._datepicker_next_month_locator).click()

    def click_day(self, day):
        """Clicks the day in the datepicker and waits for the datepicker to disappear."""
        # TODO: Throw an error if the day button is disabled
        calendar = self.selenium.find_element(*self._datepicker_calendar_locator)
        calendar.find_element(By.LINK_TEXT, str(day)).click()
        self.wait_for_datepicker_to_close()

    def select_date_from_datepicker(self, target_date):
        """Navigates to the target month in the datepicker and clicks the target day."""
        currentYear = int(self.selenium.find_element(*self._datepicker_year_locator).text)
        targetYear = target_date.year
        yearDelta = targetYear - currentYear
        monthDelta = yearDelta * 12

        months = {"January": 1,
                  "February": 2,
                  "March": 3,
                  "April": 4,
                  "May": 5,
                  "June": 6,
                  "July": 7,
                  "August": 8,
                  "September": 9,
                  "October": 10,
                  "November": 11,
                  "December": 12}
        currentMonth = months[self.selenium.find_element(*self._datepicker_month_locator).text]
        targetMonth = target_date.month
        monthDelta += targetMonth - currentMonth

        count = 0
        while (count < abs(monthDelta)):
            if monthDelta < 0:
                self.click_previous_month()
            elif monthDelta > 0:
                self.click_next_month()
            count = count + 1
        self.click_day(target_date.day)

    def type_custom_start_date(self, date_start):
        date_start_box = self.selenium.find_element(*self._custom_start_date_locator)
        date_start_box.clear()
        date_start_box.send_keys(date_start)

    def type_custom_end_date(self, date_end):
        date_end_box = self.selenium.find_element(*self._custom_end_date_locator)
        date_end_box.clear()
        date_end_box.send_keys(date_end)

    def select_custom_start_date_using_datepicker(self, date):
        self.click_start_date()
        self.select_date_from_datepicker(date)

    def select_custom_end_date_using_datepicker(self, date):
        self.click_end_date()
        self.select_date_from_datepicker(date)

    def filter_by_custom_dates_using_datepicker(self, start_date, end_date):
        """Filters by a custom date range."""
        self.enable_custom_dates()
        self.select_custom_start_date_using_datepicker(start_date)
        self.select_custom_end_date_using_datepicker(end_date)
        self.selenium.find_element(*self._set_custom_date_locator).click()

    def filter_by_custom_dates_using_keyboard(self, start_date, end_date):
        """Filters by a custom date range using any input type, not using date() format.

        This uses selenium.type_keys in an attempt to mimic actual typing

        """
        self.enable_custom_dates()
        self.type_custom_start_date(start_date)
        self.type_custom_end_date(end_date)
        self.selenium.find_element(*self._set_custom_date_locator).click()

    @property
    def is_last_day_visible(self):
        return self.is_element_visible(self._last_day_locator)

    @property
    def is_last_seven_days_visible(self):
        return self.is_element_visible(self._last_seven_days_locator)

    @property
    def is_last_thirty_days_visible(self):
        return self.is_element_visible(self._last_thirty_days_locator)

    @property
    def is_date_filter_applied(self):
        from pages.base import BasePage
        base = BasePage(self.testsetup)
        return base.date_start_from_url and base.date_end_from_url or False

    @property
    def custom_date_only_error(self):
        return self.selenium.find_element(*self._custom_date_only_error_locator).text

    @property
    def custom_date_first_error(self):
        return self.selenium.find_element(*self._custom_date_first_error_locator).text

    @property
    def custom_date_second_error(self):
        return self.selenium.find_element(*self._custom_date_second_error_locator).text

    @property
    def custom_start_date(self):
        return self.selenium.find_element(*self._custom_start_date_locator).get_attribute('value')

    @property
    def custom_end_date(self):
        return self.selenium.find_element(*self._custom_end_date_locator).get_attribute('value')
