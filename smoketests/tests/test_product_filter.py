#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittestzero import Assert
import pytest

from pages.desktop.feedback import FeedbackPage
from pages.desktop.sites import SitesPage


class TestProductFilter:

    @pytest.mark.nondestructive
    def test_feedback_can_be_filtered_by_all_products_and_versions(self, mozwebqa):
        """This testcase covers # 13602 & 13603 & 15149 in Litmus.

        1. Verify that at least three firefox versions exist
        2. Verify that filtering by version returns results
        3. Verify that the state of the filters are correct after being applied
        4. Verify product and version values in the URL

        """
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        products = feedback_pg.product_filter.products
        Assert.greater(len(products), 1)
        for product in products:
            if product != '':
                feedback_pg.product_filter.select_product(product)
                versions = feedback_pg.product_filter.versions
                [Assert.not_equal(version, "") for version in versions]
                Assert.greater(len(versions), 2)
                for version in versions:
                    feedback_pg.product_filter.select_version(version)
                    Assert.equal(feedback_pg.product_filter.selected_product, product)
                    Assert.equal(feedback_pg.product_filter.selected_version, version)
                    Assert.equal(feedback_pg.product_from_url, product)
                    Assert.equal(feedback_pg.version_from_url, version)
                    Assert.greater(len(feedback_pg.messages), 0)
                    feedback_pg.product_filter.unselect_version(version)
                feedback_pg.product_filter.unselect_product(product)
