#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random
from datetime import date, timedelta

import pytest
from unittestzero import Assert

from pages.dashboard import DashboardPage


class TestSearchDates(object):

    default_start_date = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
    default_end_date = date.today().strftime('%Y-%m-%d')

    @pytest.mark.nondestructive
    def test_preset_date_filters(self, mozwebqa):
        """Verify the preset date filters of 1, 7, and 30 days"""
        dashboard_pg = DashboardPage(mozwebqa)

        # Defaults to 7d.
        dashboard_pg.go_to_dashboard_page()
        Assert.equal(dashboard_pg.date_filter.current_days, '7d')

        # Last day filter
        dashboard_pg.date_filter.click_last_day()
        Assert.equal(dashboard_pg.date_filter.current_days, '1d')
        start_date = date.today() - timedelta(days=1)
        Assert.equal(dashboard_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range,
        # possibly by navigating to the last page and checking the
        # final result is within range. Currently blocked by bug
        # 615844.

        # Last seven days filter
        dashboard_pg.date_filter.click_last_seven_days()
        Assert.equal(dashboard_pg.date_filter.current_days, '7d')
        start_date = date.today() - timedelta(days=7)
        Assert.equal(dashboard_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range,
        # possibly by navigating to the last page and checking the
        # final result is within range. Currently blocked by bug
        # 615844.

        # Last thirty days filter
        dashboard_pg.date_filter.click_last_thirty_days()
        Assert.equal(dashboard_pg.date_filter.current_days, '30d')
        start_date = date.today() - timedelta(days=30)
        Assert.equal(dashboard_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range,
        # possibly by navigating to the last page and checking the
        # final result is within range. Currently blocked by bug
        # 615844.

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter(self, mozwebqa):
        """

        1. Verifies the calendar is displayed when filtering on custom dates
        2. Verifies date-start=<date> and end-date=<date> in the url

        """
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()

        start_date = date.today() - timedelta(days=3)
        end_date = date.today() - timedelta(days=1)

        dashboard_pg.date_filter.filter_by_custom_dates_using_datepicker(start_date, end_date)
        Assert.equal(dashboard_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        Assert.equal(dashboard_pg.date_end_from_url, end_date.strftime('%Y-%m-%d'))

        # TODO: Check results are within the expected date range,
        # possibly by navigating to the first/last pages and checking
        # the final result is within range. Currently blocked by bug
        # 615844.

        day_filters = ((1, "1d"), (7, "7d"), (30, "30d"))
        for days in day_filters:
            start_date = date.today() - timedelta(days=days[0])
            dashboard_pg.date_filter.filter_by_custom_dates_using_datepicker(start_date, date.today())
            Assert.false(dashboard_pg.date_filter.is_custom_date_filter_visible)
            Assert.equal(dashboard_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
            Assert.equal(dashboard_pg.date_end_from_url, self.default_end_date)

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_random_alphabet(self, mozwebqa):
        """Verify custom date fields do not accept alphabet"""
        # FIXME: If the server is in a different time zone than the
        # machine running this test, then "today" could be different
        # than the server default and thus this test will fail.
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()

        letters = 'abcdefghijklmnopqrstuvwxyz'
        start_date = ''.join(random.sample(letters, 8))
        end_date = ''.join(random.sample(letters, 8))

        dashboard_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(dashboard_pg.date_start_from_url, '')
        Assert.equal(dashboard_pg.date_end_from_url, '')

        dashboard_pg.date_filter.enable_custom_dates()
        Assert.equal(dashboard_pg.date_filter.custom_start_date, self.default_start_date)
        Assert.equal(dashboard_pg.date_filter.custom_end_date, self.default_end_date)

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_bad_dates(self, mozwebqa):
        """Verify random non-dates are ignored"""
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()

        start_date = random.randint(10000000, 50000000)
        end_date = random.randint(50000001, 99999999)

        def build_random_date(start, end):
            dte = random.randint(start, end)
            dte = str(dte)
            return '-'.join([dte[0:4], dte[4:6], dte[6:8]])

        data = [
            (build_random_date(10000000, 15000000), build_random_date(90000001, 99999999)),
            ('0000-00-00', '0000-00-00'),
        ]

        for start_date, end_date in data:
            dashboard_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
            Assert.equal(dashboard_pg.date_start_from_url, str(start_date))
            Assert.equal(dashboard_pg.date_end_from_url, str(end_date))

            Assert.equal(len(dashboard_pg.messages), 20)

            dashboard_pg.date_filter.enable_custom_dates()
            Assert.equal(dashboard_pg.date_filter.custom_start_date, self.default_start_date)
            Assert.equal(dashboard_pg.date_filter.custom_end_date, self.default_end_date)

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_future_dates(self, mozwebqa):
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()

        start_date = "2021-01-01"
        end_date = "2031-01-01"

        dashboard_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(dashboard_pg.date_start_from_url, start_date)
        Assert.equal(dashboard_pg.date_end_from_url, end_date)

        Assert.true(dashboard_pg.no_messages)
        Assert.equal(dashboard_pg.no_messages_message, 'No feedback matches that criteria.')

        dashboard_pg.date_filter.enable_custom_dates()
        Assert.equal(dashboard_pg.date_filter.custom_start_date, start_date)
        Assert.equal(dashboard_pg.date_filter.custom_end_date, end_date)

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_future_start_date(self, mozwebqa):
        """Verify future start date are ignored as erroneous input and
        results for a 30 day period are returned

        """
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()

        start_date = "2020-01-01"
        end_date = "2020-01-10"

        dashboard_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)

        # No messages!
        Assert.equal(dashboard_pg.total_message_count, 0)

        # Check the url bits are correct
        Assert.equal(dashboard_pg.date_start_from_url, start_date)
        Assert.equal(dashboard_pg.date_end_from_url, end_date)

        # Verify the dates
        dashboard_pg.date_filter.enable_custom_dates()
        Assert.equal(dashboard_pg.date_filter.custom_start_date, start_date)
        Assert.equal(dashboard_pg.date_filter.custom_end_date, end_date)

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_end_date_lower_than_start_date(self, mozwebqa):
        """Verify start_date > end_date get switched automatically and the
        results are shown from end date to start date

        """
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()

        start_date = date.today() - timedelta(days=1)
        end_date = date.today() - timedelta(days=3)

        dashboard_pg.date_filter.filter_by_custom_dates_using_datepicker(start_date, end_date)
        Assert.equal(dashboard_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        Assert.equal(dashboard_pg.date_end_from_url, end_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range,
        # possibly by navigating to the first/last pages and checking
        # the final result is within range. Currently blocked by bug
        # 615844.

        # Test that the dates in the date filter are reordered chronologically
        dashboard_pg.date_filter.enable_custom_dates()
        Assert.equal(dashboard_pg.date_filter.custom_start_date, end_date.strftime('%Y-%m-%d'))
        Assert.equal(dashboard_pg.date_filter.custom_end_date, start_date.strftime('%Y-%m-%d'))
