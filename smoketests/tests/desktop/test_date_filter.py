#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import date, timedelta
import random

from unittestzero import Assert
import pytest

from pages.desktop.feedback import FeedbackPage

xfail = pytest.mark.xfail


class TestSearchDates:

    @pytest.mark.nondestructive
    def test_feedback_preset_date_filters(self, mozwebqa):
        """This testcase covers # 13605 & 13606 in Litmus.

        1. Verifies the preset date filters of 1, 7, and 30 days

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        Assert.equal(feedback_pg.date_filter.current_days, u"\u221e")

        # Last day filter
        Assert.equal(feedback_pg.date_filter.last_day_tooltip, 'Last day')
        feedback_pg.date_filter.click_last_day()
        Assert.equal(feedback_pg.date_filter.current_days, '1d')
        start_date = date.today() - timedelta(days=1)
        Assert.equal(feedback_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range, possibly by navigating to the last page and checking the final result is within range. Currently blocked by bug 615844.

        # Last seven days filter
        Assert.equal(feedback_pg.date_filter.last_seven_days_tooltip, 'Last 7 days')
        feedback_pg.date_filter.click_last_seven_days()
        Assert.equal(feedback_pg.date_filter.current_days, '7d')
        start_date = date.today() - timedelta(days=7)
        Assert.equal(feedback_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range, possibly by navigating to the last page and checking the final result is within range. Currently blocked by bug 615844.

        # Last thirty days filter
        Assert.equal(feedback_pg.date_filter.last_thirty_days_tooltip, 'Last 30 days')
        feedback_pg.date_filter.click_last_thirty_days()
        Assert.equal(feedback_pg.date_filter.current_days, '30d')
        start_date = date.today() - timedelta(days=30)
        Assert.equal(feedback_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range, possibly by navigating to the last page and checking the final result is within range. Currently blocked by bug 615844.

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter(self, mozwebqa):
        """This testcase covers # 13605, 13606 & 13715 in Litmus.

        1. Verifies the calendar is displayed when filtering on custom dates
        2. Verifies date-start=<date> and end-date=<date> in the url

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        Assert.equal(feedback_pg.date_filter.custom_dates_tooltip, "Custom")

        start_date = date.today() - timedelta(days=3)
        end_date = date.today() - timedelta(days=1)

        feedback_pg.date_filter.filter_by_custom_dates_using_datepicker(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        Assert.equal(feedback_pg.date_end_from_url, end_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range, possibly by navigating to the first/last pages and checking the final result is within range. Currently blocked by bug 615844.

        # Check that the relevant days preset link is highlighted when the applied custom date filter matches it
        day_filters = ((1, "1d"), (7, "7d"), (30, "30d"))
        for days in day_filters:
            start_date = date.today() - timedelta(days=days[0])
            feedback_pg.date_filter.filter_by_custom_dates_using_datepicker(start_date, date.today())
            Assert.false(feedback_pg.date_filter.is_custom_date_filter_visible)
            Assert.equal(feedback_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
            Assert.equal(feedback_pg.date_end_from_url, date.today().strftime('%Y-%m-%d'))
            Assert.equal(feedback_pg.date_filter.current_days, days[1])

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_random_alphabet(self, mozwebqa):
        """This testcase covers # 13607 in Litmus.

        1.Verifies custom date fields do not accept alphabet

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()

        letters = 'abcdefghijklmnopqrstuvwxyz'
        start_date = ''.join(random.sample(letters, 8))
        end_date = ''.join(random.sample(letters, 8))

        feedback_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, '')
        Assert.equal(feedback_pg.date_end_from_url, '')

        feedback_pg.date_filter.click_custom_dates()
        Assert.equal(feedback_pg.date_filter.custom_start_date, '')
        Assert.equal(feedback_pg.date_filter.custom_end_date, '')

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_random_numbers(self, mozwebqa):
        """This testcase covers # 13608 in Litmus.

        1.Verifies random numbers show all recent feedback

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()

        start_date = random.randint(10000000, 50000000)
        end_date = random.randint(50000001, 99999999)

        feedback_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, str(start_date))
        Assert.equal(feedback_pg.date_end_from_url, str(end_date))

        Assert.equal(len(feedback_pg.messages), 20)

        feedback_pg.date_filter.click_custom_dates()
        Assert.equal(feedback_pg.date_filter.custom_start_date, str(start_date))
        Assert.equal(feedback_pg.date_filter.custom_end_date, str(end_date))

    @pytest.mark.nondestructive 
    def test_feedback_custom_date_filter_with_invalid_dates(self, mozwebqa):
        """This testcase covers # 13609 & 13725 in Litmus.

        1.Verifies invalid dates show all recent feedback

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()

        start_date = "0000-00-00"
        end_date = "0000-00-00"

        feedback_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, start_date)
        Assert.equal(feedback_pg.date_end_from_url, end_date)

        Assert.equal(len(feedback_pg.messages), 20)

        feedback_pg.date_filter.click_custom_dates()
        Assert.equal(feedback_pg.date_filter.custom_start_date, start_date)
        Assert.equal(feedback_pg.date_filter.custom_end_date, end_date)

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_future_dates(self, mozwebqa):
        """This testcase covers # 13612 in Litmus.

        1.Verifies future dates generate an error

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()

        start_date = "2021-01-01"
        end_date = "2031-01-01"

        feedback_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, start_date)
        Assert.equal(feedback_pg.date_end_from_url, end_date)

        Assert.equal(feedback_pg.warning_heading, 'NO SEARCH RESULTS FOUND.')

        feedback_pg.date_filter.click_custom_dates()
        Assert.equal(feedback_pg.date_filter.custom_start_date, start_date)
        Assert.equal(feedback_pg.date_filter.custom_end_date, end_date)

    @xfail(reason="Bug 686850 - Returned message counts vary too much to reliably test")
    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_future_start_date(self, mozwebqa):
        """This testcase covers # 13610 in Litmus.

        1.Verifies future start date are ignored as erroneous input and results for a 30 day period are returned

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()

        start_date = "2900-01-01"
        end_date = ""

        feedback_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, start_date)
        Assert.equal(feedback_pg.date_end_from_url, end_date)

        Assert.equal(len(feedback_pg.messages), 20)

        feedback_pg.date_filter.click_custom_dates()
        Assert.equal(feedback_pg.date_filter.custom_start_date, start_date)
        Assert.equal(feedback_pg.date_filter.custom_end_date, end_date)

    @xfail(reason="Bug 686850 - Returned message counts vary too much to reliably test")
    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_future_end_date(self, mozwebqa):
        """This testcase covers # 13611 in Litmus.

        1. Verifies future end date filter data until current day

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()

        start_date = ""
        end_date = "2900-01-01"

        feedback_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, start_date)
        Assert.equal(feedback_pg.date_end_from_url, end_date)

        Assert.equal(feedback_pg.message_column_heading, 'SEARCH RESULTS')

        feedback_pg.date_filter.click_custom_dates()
        Assert.equal(feedback_pg.date_filter.custom_start_date, start_date)
        Assert.equal(feedback_pg.date_filter.custom_end_date, end_date)

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_end_date_lower_than_start_date(self, mozwebqa):
        """This testcase covers # 13613, 13724 in Litmus.

        1. Verifies start_date > end_date get switched automatically and the results are shown from end date to start date

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()

        start_date = date.today() - timedelta(days=1)
        end_date = date.today() - timedelta(days=3)

        feedback_pg.date_filter.filter_by_custom_dates_using_datepicker(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, start_date.strftime('%Y-%m-%d'))
        Assert.equal(feedback_pg.date_end_from_url, end_date.strftime('%Y-%m-%d'))
        # TODO: Check results are within the expected date range, possibly by navigating to the first/last pages and checking the final result is within range. Currently blocked by bug 615844.

        feedback_pg.date_filter.click_custom_dates()
        Assert.equal(feedback_pg.date_filter.custom_start_date, start_date.strftime('%Y-%m-%d'))
        Assert.equal(feedback_pg.date_filter.custom_end_date, end_date.strftime('%Y-%m-%d'))

    @pytest.mark.nondestructive
    def test_feedback_custom_date_filter_with_mdy_format(self, mozwebqa):
        """This testcase covers # 13614 in Litmus.

        1.Verifies custom date fields show all recent feedback

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()

        start_date = '04-22-2011'
        end_date = ''

        feedback_pg.date_filter.filter_by_custom_dates_using_keyboard(start_date, end_date)
        Assert.equal(feedback_pg.date_start_from_url, start_date)
        Assert.equal(feedback_pg.date_end_from_url, '')

        Assert.equal(len(feedback_pg.messages), 20)

        feedback_pg.date_filter.click_custom_dates()
        Assert.equal(feedback_pg.date_filter.custom_start_date, start_date)
        Assert.equal(feedback_pg.date_filter.custom_end_date, '')

    @pytest.mark.nondestructive
    def test_dashboard_should_have_recent_feedback(self, mozwebqa):
        """This testcase covers https://bugzilla.mozilla.org/show_bug.cgi?id=816213

        1. Verifies that there are results for the 1 day date range

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        feedback_pg.date_filter.click_last_day()
        Assert.equal(feedback_pg.date_filter.current_days, '1d')
        Assert.true(len(feedback_pg.messages) > 0, 'There is no feedback for the past day on the dashboard.')
