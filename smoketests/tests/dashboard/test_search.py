# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from unittestzero import Assert

from pages.dashboard import DashboardPage


class TestSearch(object):

    @pytest.mark.nondestructive
    def test_that_empty_search_of_feedback_returns_some_data(self, mozwebqa):
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for('')
        Assert.greater(len(dashboard_pg.messages), 0)

    @pytest.mark.nondestructive
    def test_that_we_can_search_feedback_with_unicode(self, mozwebqa):
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(u"p\xe1gina")
        # There's no way to guarantee that the search we did finds
        # responses on the page. So we check for one of two possible
        # scenarios: existences of responses or a message count of 0.
        Assert.true(
            dashboard_pg.no_messages
            or (len(dashboard_pg.messages) > 0)
        )
