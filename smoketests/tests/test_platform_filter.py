#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittestzero import Assert
import pytest

from pages.desktop.feedback import FeedbackPage


class TestPlatformFilter:

    @pytest.mark.nondestructive
    def test_feedback_can_be_filtered_by_platform(self, mozwebqa):
        """This testcase covers # 15215 in Litmus.

        1. Verify that the selected platform is the only one to appear in the list and is selected
        2. Verify that the number of messages in the platform list is plus or minus 15 for the number of messages returned
        3. Verify that the platform appears in the URL
        4. Verify that the platform for all messages on the first page of results is correct

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        feedback_pg.product_filter.select_product('firefox')

        platform_name = "OS X"
        platform = feedback_pg.platform_filter.platform(platform_name)
        platform_message_count = platform.message_count
        platform_code = platform.code
        platform.click()

        total_message_count = feedback_pg.total_message_count
        message_count_difference = total_message_count - platform_message_count

        Assert.equal(len(feedback_pg.platform_filter.platforms), 1)
        Assert.true(feedback_pg.platform_filter.platform(platform_name).is_selected)
        # TODO refactor if unittest-zero receives an Assert.within_range method
        Assert.less_equal(message_count_difference, 15)
        Assert.greater_equal(message_count_difference, -15)
        Assert.equal(feedback_pg.platform_from_url, platform_code)
        [Assert.equal(message.platform, platform_name) for message in feedback_pg.messages]
