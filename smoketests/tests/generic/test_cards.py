# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.generic_feedback_form import GenericFeedbackFormPage


class TestCards(object):
    @pytest.mark.nondestructive
    def test_back_and_forth(self, mozwebqa):
        """Test back buttons"""
        desc = 'input-tests testing'

        # 1. go to the feedback form
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. click back and click sad
        feedback_pg.click_back()
        feedback_pg.click_sad_feedback()

        # 4. verify submit button is disabled
        assert feedback_pg.is_submit_enabled is False

        # 5. fill out description, check submit button enabled
        feedback_pg.set_description(desc)
        assert feedback_pg.is_submit_enabled
