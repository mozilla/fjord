# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.dashboard import DashboardPage


class TestLocaleFilter(object):

    @pytest.mark.nondestructive
    def test_feedback_can_be_filtered_by_locale(self, mozwebqa):
        """Tests locale filtering in dashboard

        1. Verify we see at least one locale
        2. Select that locale
        3. Verify number of messages in locale is less than total number of messages
        4. Verify locale short code appears in the URL
        5. Verify that the locale for all messages on the first page of results is correct

        """
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()
        total_messages = dashboard_pg.total_message_count

        locales = dashboard_pg.locale_filter.locales
        locale_names = [locale.name for locale in locales]

        assert len(locales) > 0

        for name in locale_names[:2]:
            locale = dashboard_pg.locale_filter.locale(name)

            locale_name = locale.name
            locale_code = locale.code
            locale_count = locale.message_count
            assert total_messages > locale_count

            dashboard_pg.locale_filter.select_locale(locale_code)

            assert total_messages > dashboard_pg.total_message_count
            assert len(dashboard_pg.locale_filter.locales) == 1
            assert dashboard_pg.locale_filter.selected_locale.name == locale_name
            assert dashboard_pg.locale_from_url == locale_code

            for message in dashboard_pg.messages:
                assert message.locale == locale_name

            dashboard_pg.locale_filter.unselect_locale(locale_code)
