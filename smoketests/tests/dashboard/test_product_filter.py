# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from unittestzero import Assert

from pages.dashboard import DashboardPage


class TestProductFilter(object):
    @pytest.mark.nondestructive
    def test_feedback_can_be_filtered_by_all_products_and_versions(self, mozwebqa):
        """Tests product filtering in dashboard

        1. Verify that at least one product exists
        2. Verify that filtering by product returns results
        3. Verify that versions show up when you choose a product
        4. Verify that the state of the filters are correct after being applied
        5. Verify product and version values in the URL

        NB: We don't cycle through all product/version
        combinations--only the first two of each.

        """
        dashboard_pg = DashboardPage(mozwebqa)

        dashboard_pg.go_to_dashboard_page()

        total_messages = dashboard_pg.total_message_count

        products = dashboard_pg.product_filter.products
        Assert.greater(len(products), 0)

        for product in products[:2]:
            if not product:
                # If it's the "unknown" product, just skip it.
                continue

            dashboard_pg.product_filter.select_product(product)
            Assert.greater(total_messages, dashboard_pg.total_message_count)
            versions = dashboard_pg.product_filter.versions
            Assert.greater(len(versions), 0)

            for version in versions[:2]:
                if not version:
                    # If it's the "unknown" version, just skip it.
                    continue

                dashboard_pg.product_filter.select_version(version)

                Assert.greater(total_messages, dashboard_pg.total_message_count)
                Assert.equal(dashboard_pg.product_filter.selected_product, product)
                Assert.equal(dashboard_pg.product_filter.selected_version, version)
                Assert.equal(dashboard_pg.product_from_url, product)
                Assert.equal(dashboard_pg.version_from_url, version)
                Assert.greater(len(dashboard_pg.messages), 0)
                dashboard_pg.product_filter.unselect_version(version)

            dashboard_pg.product_filter.unselect_product(product)
