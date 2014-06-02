#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittestzero import Assert
import pytest

from pages.desktop.sites import SitesPage


class TestSimilarMessages:

    @pytest.mark.nondestructive
    def test_similar_messages(self, mozwebqa):
        """This testcase covers # 13807 in Litmus."""
        sites_pg = SitesPage(mozwebqa)

        sites_pg.go_to_sites_page()
        sites_pg.product_filter.select_product('firefox')
        sites_pg.product_filter.select_version(2)

        #store the first site's name and click it
        site = sites_pg.sites[0]
        site_name = site.name
        themes_pg = site.click_name()

        #click similar messages and navigate to the second page
        theme_pg = themes_pg.themes[0].click_similar_messages()
        theme_pg.click_next_page()

        Assert.equal(theme_pg.messages_heading, 'THEME')
        Assert.equal(theme_pg.page_from_url, 2)
        Assert.equal(theme_pg.theme_callout, 'Theme for %s' % site_name.lower())
        Assert.greater(len(theme_pg.messages), 0)
        Assert.equal(theme_pg.back_link, u'Back to %s \xbb' % site_name.lower())
        [Assert.contains(site_name.lower(), message.site) for message in theme_pg.messages]
