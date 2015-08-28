# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittestzero import Assert

from pages.picker import PickerPage


class TestPicker(object):
    def test_picker_to_form_to_picker(self, mozwebqa):
        # Go to /feedback/, verify product picker page comes up, and
        # verify there are products on it
        picker_pg = PickerPage(mozwebqa)
        picker_pg.go_to_picker_page()

        # We can't guarantee which products are in the list or what
        # order they're in, so we do this goofy thing where we make
        # sure it's greater than one and hope "Firefox" is one of
        # them
        products = picker_pg.products
        Assert.greater(len(products), 0)
        names = [prod.name for prod in products]
        assert 'Firefox' in names

        # Pick the first product that's not "Firefox" since that's a
        # substring of many of the product names
        product = [prod for prod in picker_pg.products if prod.name != 'Firefox'][0]
        product_name = product.name
        feedback_pg = product.click()

        Assert.true(feedback_pg.is_the_current_page)

        # Verify this feedback form is for the product we chose
        Assert.true(feedback_pg.is_product(product_name))

        # Go back to the product picker
        picker_pg = feedback_pg.go_to_picker_page()
        products = picker_pg.products
        Assert.greater(len(products), 0)
