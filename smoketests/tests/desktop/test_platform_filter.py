# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from unittestzero import Assert

from pages.desktop.feedback import FeedbackPage


class TestPlatformFilter(object):

    @pytest.mark.nondestructive
    def test_feedback_can_be_filtered_by_platform(self, mozwebqa):
        """Tests platform filtering in dashboard

        1. Verify that the selected platform is the only one to appear in the list and is selected
        2. Verify that the number of messages is less than the total messages
        3. Verify that the platform appears in the URL
        4. Verify that the platform for all messages on the first page of results is correct

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        total_messages = feedback_pg.total_message_count

        platforms = feedback_pg.platform_filter.platforms
        platform_names = [platform.name for platform in platforms]

        Assert.greater(len(platforms), 0)

        for name in platform_names[:2]:
            platform = feedback_pg.platform_filter.platform(name)

            platform_name = platform.name
            platform_code = platform.code

            platform_count = platform.message_count
            Assert.greater(total_messages, platform_count)

            feedback_pg.platform_filter.select_platform(platform_code)

            Assert.greater(total_messages, feedback_pg.total_message_count)
            Assert.equal(len(feedback_pg.platform_filter.platforms), 1)
            Assert.equal(feedback_pg.platform_filter.selected_platform.name, platform_name)
            Assert.equal(feedback_pg.platform_from_url, platform_code)

            for message in feedback_pg.messages:
                Assert.equal(message.platform, platform_name)

            feedback_pg.platform_filter.unselect_platform(platform_code)
