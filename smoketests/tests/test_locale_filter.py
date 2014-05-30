#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from unittestzero import Assert

from pages.desktop.feedback import FeedbackPage


class TestLocaleFilter(object):

    @pytest.mark.nondestructive
    def test_feedback_can_be_filtered_by_locale(self, mozwebqa):
        """This testcase covers # 15120 in Litmus.

        1. Verify we see at least one locale
        2. Select that locale
        3. Verify number of messages in locale is less than total number of messages
        4. Verify locale short code appears in the URL
        5. Verify that the locale for all messages on the first page of results is correct

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        total_messages = feedback_pg.total_message_count

        locales = feedback_pg.locale_filter.locales
        locale_names = [locale.name for locale in locales]

        Assert.greater_equal(len(locales), 1)

        for name in locale_names[:2]:
            locale = feedback_pg.locale_filter.locale(name)

            locale_name = locale.name
            locale_code = locale.code
            locale_count = locale.message_count
            Assert.greater(total_messages, locale_count)

            feedback_pg.locale_filter.select_locale(locale_code)

            Assert.greater(total_messages, feedback_pg.total_message_count)
            Assert.equal(len(feedback_pg.locale_filter.locales), 1)
            Assert.equal(feedback_pg.locale_filter.selected_locale.name, locale_name)
            Assert.equal(feedback_pg.locale_from_url, locale_code)

            for message in feedback_pg.messages:
                Assert.equal(message.locale, locale_name)

            feedback_pg.locale_filter.unselect_locale(locale_code)
