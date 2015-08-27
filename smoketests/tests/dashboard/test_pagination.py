# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.dashboard import DashboardPage


class TestPagination:
    SEARCH_TERM = u'firefox'

    @pytest.mark.nondestructive
    def test_search_pagination(self, mozwebqa):
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        # Set the date range to 2013-01-01 -> today so that we're more
        # likely to have so many messages in the results that it
        # paginates. Otherwise it might not paginate on stage or local
        # environments.
        dashboard_pg.set_date_range('2013-01-01')
        dashboard_pg.search_for(self.SEARCH_TERM)

        # Check the total message count. If it's less than 50 (two
        # pages worth), then we will fail with a helpful message.
        assert dashboard_pg.total_message_count >= 50, 'Not enough data to test. Add more data.'

        assert dashboard_pg.is_older_messages_link_visible is True
        assert dashboard_pg.is_newer_messages_link_visible is False
        assert dashboard_pg.older_messages_link == 'Older Messages'

        dashboard_pg.click_older_messages()
        assert dashboard_pg.search_term_from_url == self.SEARCH_TERM

        assert dashboard_pg.is_older_messages_link_visible is True
        assert dashboard_pg.is_newer_messages_link_visible is True
        assert dashboard_pg.older_messages_link == 'Older Messages'
        assert dashboard_pg.newer_messages_link == 'Newer Messages'
        assert dashboard_pg.page_from_url == 2

        dashboard_pg.click_newer_messages()
        assert dashboard_pg.search_term_from_url == self.SEARCH_TERM

        assert dashboard_pg.is_older_messages_link_visible is True
        assert dashboard_pg.is_newer_messages_link_visible is False
        assert dashboard_pg.older_messages_link == 'Older Messages'
        assert dashboard_pg.page_from_url == 1
