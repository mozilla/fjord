#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from unittestzero import Assert
import pytest

from pages.desktop.submit_idea import SubmitIdeaPage


class TestSubmitIdea:

    def test_submitting_idea(self, mozwebqa):
        """This testcase covers # 15104 in Litmus.

        1. Verifies the thank you page is loaded

        """
        submit_idea_pg = SubmitIdeaPage(mozwebqa)

        submit_idea_pg.go_to_submit_idea_page()
        idea = 'Automated idea %s' % str(time.time()).split('.')[0]
        submit_idea_pg.type_feedback(idea)
        thanks_pg = submit_idea_pg.submit_feedback()
        Assert.true(thanks_pg.is_the_current_page)

    def test_submitting_idea_with_unicode_characters(self, mozwebqa):
        """This testcase covers # 15061 in Litmus.

        1. Verifies the thank you page is loaded

        """
        submit_idea_pg = SubmitIdeaPage(mozwebqa)

        submit_idea_pg.go_to_submit_idea_page()
        idea = u'Automated idea with unicode \u2603 %s' % str(time.time()).split('.')[0]
        submit_idea_pg.type_feedback(idea)
        thanks_pg = submit_idea_pg.submit_feedback()
        Assert.true(thanks_pg.is_the_current_page)

    @pytest.mark.nondestructive
    def test_remaining_character_count(self, mozwebqa):
        """This testcase covers # 15029 in Litmus.

        1. Verifies the remaining character count decreases
        2. Verifies that the remaining character count style changes at certain thresholds
        3. Verified that the 'Submit Feedback' button is disabled when character limit is exceeded

        """
        submit_idea_pg = SubmitIdeaPage(mozwebqa)

        submit_idea_pg.go_to_submit_idea_page()
        Assert.equal(submit_idea_pg.remaining_character_count, 250)
        Assert.false(submit_idea_pg.is_remaining_character_count_limited)
        Assert.false(submit_idea_pg.is_remaining_character_count_negative)
        Assert.false(submit_idea_pg.is_submit_feedback_enabled)

        submit_idea_pg.type_feedback("a" * 199)
        Assert.equal(submit_idea_pg.remaining_character_count, 51)
        Assert.false(submit_idea_pg.is_remaining_character_count_limited)
        Assert.false(submit_idea_pg.is_remaining_character_count_negative)
        Assert.true(submit_idea_pg.is_submit_feedback_enabled)

        submit_idea_pg.type_feedback("b")
        Assert.equal(submit_idea_pg.remaining_character_count, 50)
        Assert.true(submit_idea_pg.is_remaining_character_count_limited)
        Assert.false(submit_idea_pg.is_remaining_character_count_negative)
        Assert.true(submit_idea_pg.is_submit_feedback_enabled)

        submit_idea_pg.type_feedback("c" * 50)
        Assert.equal(submit_idea_pg.remaining_character_count, 0)
        Assert.true(submit_idea_pg.is_remaining_character_count_limited)
        Assert.false(submit_idea_pg.is_remaining_character_count_negative)
        Assert.true(submit_idea_pg.is_submit_feedback_enabled)

        submit_idea_pg.type_feedback("d")
        Assert.equal(submit_idea_pg.remaining_character_count, -1)
        Assert.false(submit_idea_pg.is_remaining_character_count_limited)
        Assert.true(submit_idea_pg.is_remaining_character_count_negative)
        Assert.false(submit_idea_pg.is_submit_feedback_enabled)

    def test_submitting_same_idea_twice_generates_error_message(self, mozwebqa):
        """This testcase covers # 15119 in Litmus.

        1. Verifies feedback submission fails if the same feedback is submitted within a 5 minute window.

        """
        idea = 'Automated idea %s' % str(time.time()).split('.')[0]
        submit_idea_pg = SubmitIdeaPage(mozwebqa)

        submit_idea_pg.go_to_submit_idea_page()
        submit_idea_pg.type_feedback(idea)
        thanks_pg = submit_idea_pg.submit_feedback()
        Assert.true(thanks_pg.is_the_current_page)

        submit_idea_pg.go_to_submit_idea_page()
        submit_idea_pg.type_feedback(idea)
        submit_idea_pg.submit_feedback(expected_result='failure')
        Assert.equal(submit_idea_pg.error_message, 'We already got your feedback! Thanks.')
