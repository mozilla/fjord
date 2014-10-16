# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from unittestzero import Assert

from pages.generic_feedback_form import GenericFeedbackFormPage


class TestCards(object):
    @pytest.mark.nondestructive
    def test_back_and_forth(self, mozwebqa):
        """Test next and back buttons"""
        desc = 'input-tests testing'

        # 1. go to the feedback form
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. click back and happy again
        feedback_pg.click_moreinfo_back()
        feedback_pg.click_happy_feedback()

        # 4. check next button is disabled, fill out description,
        # check next button is enabled and move on
        Assert.false(feedback_pg.is_moreinfo_next_enabled)
        feedback_pg.set_description(desc)
        Assert.true(feedback_pg.is_moreinfo_next_enabled)
        feedback_pg.click_moreinfo_next()

        # 5. click back and next again
        feedback_pg.click_email_back()
        feedback_pg.click_moreinfo_next()
