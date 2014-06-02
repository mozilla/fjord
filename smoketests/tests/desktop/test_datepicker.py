#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import date

from unittestzero import Assert
import pytest

from pages.desktop.feedback import FeedbackPage


class TestDatePicker:

    @pytest.mark.nondestructive
    def test_datepicker_is_only_shown_when_a_date_field_has_focus(self, mozwebqa):
        """This testcase covers # 13726 in Litmus.

        1.Verify that two text fields appear to set the start and end dates
        2.On clicking inside the date text field a calendar should pop up to select the date
        3.Calendar pop up gets closed
        4.Selected date is set in the date field and calendar pop up gets closed

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        Assert.false(feedback_pg.date_filter.is_datepicker_visible)
        feedback_pg.date_filter.click_custom_dates()

        #Check that two text fields appear to set the start and end dates
        Assert.true(feedback_pg.date_filter.is_custom_start_date_visible)
        Assert.true(feedback_pg.date_filter.is_custom_end_date_visible)

        #Check if clicking inside the start/end date text field a calendar pops up
        feedback_pg.date_filter.click_start_date()
        Assert.true(feedback_pg.date_filter.is_datepicker_visible)
        #dismiss the datepicker and assert that it is not visible before clicking in the end date field
        feedback_pg.date_filter.close_datepicker()
        Assert.false(feedback_pg.date_filter.is_datepicker_visible)
        feedback_pg.date_filter.click_end_date()
        Assert.true(feedback_pg.date_filter.is_datepicker_visible)

        #Check if clicking outside of calendar pop up makes it disappear
        feedback_pg.date_filter.close_datepicker()
        Assert.false(feedback_pg.date_filter.is_datepicker_visible)

    @pytest.mark.nondestructive
    def test_selecting_date_from_datepicker_populates_text_field(self, mozwebqa):
        """This testcase covers # 13844 in Litmus.

        1. On clicking inside the date text field a calendar should pop up to
        select the date. Verify that selected date appears in the date field.

        """
        feedback_pg = FeedbackPage(mozwebqa)

        today_date = date.today()

        feedback_pg.go_to_feedback_page()
        feedback_pg.date_filter.click_custom_dates()
        feedback_pg.date_filter.click_start_date()
        feedback_pg.date_filter.click_day(today_date.day)
        Assert.equal(feedback_pg.date_filter.custom_start_date, today_date.strftime('%Y-%m-%d'))
        feedback_pg.date_filter.click_end_date()
        feedback_pg.date_filter.click_day(today_date.day)
        Assert.equal(feedback_pg.date_filter.custom_end_date, today_date.strftime('%Y-%m-%d'))

    @pytest.mark.nondestructive
    def test_datepicker_next_month_button_disabled(self, mozwebqa):
        """This testcase covers # 13844 in Litmus.

        1. The forward button of the calendar pop up is disabled if the user
        is in current month thus unable to select some future date.

        """
        feedback_pg = FeedbackPage(mozwebqa)
        feedback_pg.go_to_feedback_page()
        feedback_pg.date_filter.click_custom_dates()
        feedback_pg.date_filter.click_start_date()
        Assert.true(feedback_pg.date_filter.is_datepicker_next_month_button_disabled)

        feedback_pg.date_filter.click_end_date()
        Assert.true(feedback_pg.date_filter.is_datepicker_next_month_button_disabled)
