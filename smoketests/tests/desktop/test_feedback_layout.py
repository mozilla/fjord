#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittestzero import Assert
import pytest

from pages.desktop.feedback import FeedbackPage

xfail = pytest.mark.xfail


class Test_Feedback_Layout:
    """Litmus 13593 - input:Verify the layout of homepage."""

    @pytest.mark.nondestructive
    def test_the_header_layout(self, mozwebqa):
        """This testcase covers # 13594 & 13599 in Litmus.

        Litmus 13594 - input:Verify the layout of header area
        Litmus 13599 - input:Check the links in header area

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        feedback_pg.header.click_feedback_link()
        Assert.true(feedback_pg.is_the_current_page)

        themes_pg = feedback_pg.header.click_themes_link()
        Assert.true(themes_pg.is_the_current_page)
        feedback_pg.go_to_feedback_page()

        sites_pg = feedback_pg.header.click_sites_link()
        Assert.true(sites_pg.is_the_current_page)
        feedback_pg.go_to_feedback_page()

        feedback_pg.header.click_main_heading_link()
        Assert.true(feedback_pg.is_the_current_page)

    @pytest.mark.nondestructive
    def test_the_area_layout(self, mozwebqa):
        """This testcase covers # 13598 in Litmus.

        Litmus 13598 - input:Verify the layout of footer area.

        """
        feedback_pg = FeedbackPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        Assert.equal(feedback_pg.footer.privacy_policy, "Privacy Policy")
        Assert.equal(feedback_pg.footer.legal_notices, "Legal Notices")
        Assert.equal(feedback_pg.footer.report_trademark_abuse, "Report Trademark Abuse")
        Assert.equal(feedback_pg.footer.unless_otherwise_noted, "noted")
        Assert.equal(feedback_pg.footer.creative_commons, "Creative Commons Attribution Share-Alike License v3.0")
        Assert.equal(feedback_pg.footer.about_input, "About Firefox Input")
        Assert.true(feedback_pg.footer.is_language_dropdown_visible)

    @xfail(reason="Bug 720191 - [prod] Platform section: Android is listed as a Desktop platform")
    @pytest.mark.nondestructive
    def test_the_left_panel_layout(self, mozwebqa):
        """This testcase covers # 13595 & 13600 in Litmus.

        Litmus 13595 - input:Verify the layout of the left hand side section containing various filtering options
        Litmus 13600 - input:Verify the applications drop down in Product

        """
        feedback_pg = FeedbackPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        Assert.equal(feedback_pg.product_filter.selected_product, 'firefox')
        Assert.equal(feedback_pg.product_filter.selected_version, '7.0')
        Assert.false(feedback_pg.date_filter.is_date_filter_applied)

        Assert.false(feedback_pg.date_filter.is_custom_date_filter_visible)

        feedback_pg.date_filter.click_custom_dates()

        Assert.greater(len(feedback_pg.platform_filter.platforms), 0)
        Assert.equal(feedback_pg.product_filter.products, ['firefox', 'mobile'])
        feedback_pg.product_filter.select_version('--')
        types = [type.name for type in feedback_pg.type_filter.types]
        Assert.equal(types, ['Praise', 'Issues', 'Ideas'])

        platforms = [platform.name for platform in feedback_pg.platform_filter.platforms]
        Assert.equal(platforms, ['Windows 7', 'Windows XP', 'Windows Vista', 'Mac OS X', 'Linux'])

        Assert.greater(len(feedback_pg.locale_filter.locales), 0)

        locales = [locale.name for locale in feedback_pg.locale_filter.locales]
        Assert.true(set(['English (US)', 'German', 'Spanish', 'French']).issubset(set(locales)))

    @pytest.mark.nondestructive
    def test_the_middle_section_page(self, mozwebqa):
        """This testcase covers # 13599 & 13721 in Litmus.

        Litmus 13596 - input:Verify the layout of Latest Feedback section
        Litmus 13721 - input:Verify the layout of Feedback page (feedback tab)

        """
        feedback_pg = FeedbackPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        Assert.equal(feedback_pg.search_box_placeholder, "Search by keyword")
        Assert.greater(len(feedback_pg.messages), 0)

        Assert.true(feedback_pg.is_chart_visible)

        Assert.true(feedback_pg.is_older_messages_link_enabled)
        Assert.false(feedback_pg.is_newer_messages_link_enabled)

        feedback_pg.click_older_messages()
        Assert.true(feedback_pg.is_older_messages_link_enabled)
        Assert.true(feedback_pg.is_newer_messages_link_enabled)

        feedback_pg.click_newer_messages()
        Assert.true(feedback_pg.is_older_messages_link_enabled)
        Assert.false(feedback_pg.is_newer_messages_link_enabled)

    @xfail(reason="Bug 659640 - [Input] 'While visiting' section is not shown on the homepage")
    @pytest.mark.nondestructive
    def test_the_right_panel_layout(self, mozwebqa):
        """This testcase covers # 13597 & 13716 in Litmus.

        Litmus 13597 - input:Verify the layout of right hand section containing statistics data
        Litmus 13716 - input:Verify while visiting section

        """
        feedback_pg = FeedbackPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        Assert.equal(feedback_pg.total_message_count_heading, "MESSAGES")
        Assert.greater(feedback_pg.total_message_count, 0)

        Assert.equal(feedback_pg.common_words_filter.common_words_header, "Often Mentioned")
        Assert.greater(feedback_pg.common_words_filter.common_words_count, 0)

        Assert.equal(feedback_pg.sites_filter.header, "While Visiting")
        Assert.greater(len(feedback_pg.sites_filter.sites), 0)
