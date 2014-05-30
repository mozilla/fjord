# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittestzero import Assert


class TestFeedback:

    @pytest.mark.xfail(reason='Functionality missing - prevent multiply submission')
    def test_submitting_same_feedback_twice(self, mozwebqa):
        """This testcase covers # 15119 in Litmus.

        1. Verifies feedback submission fails if the same feedback is submitted within a 5 minute window.

        """
        text = 'I submit this feedback twice within a five minute window and it should fail.'

        from pages.desktop.submit_happy_feedback import SubmitHappyFeedbackPage
        submit_happy_feedback_pg = SubmitHappyFeedbackPage(mozwebqa)

        submit_happy_feedback_pg.go_to_submit_happy_feedback_page()
        submit_happy_feedback_pg.type_feedback(text)
        thanks_pg = submit_happy_feedback_pg.submit_feedback()
        Assert.true(thanks_pg.is_the_current_page)

        submit_happy_feedback_pg.go_to_submit_happy_feedback_page()
        submit_happy_feedback_pg.type_feedback(text)
        submit_happy_feedback_pg.submit_feedback()
        Assert.equal(submit_happy_feedback_pg.error_message, 'We already got your feedback! Thanks.')

    def test_submitting_feedback_with_unicode_characters(self, mozwebqa):
        """This testcase covers # 15061 in Litmus.

        1. Verifies the thank you page is loaded

        """
        from pages.desktop.submit_happy_feedback import SubmitHappyFeedbackPage
        submit_happy_feedback_pg = SubmitHappyFeedbackPage(mozwebqa)

        submit_happy_feedback_pg.go_to_submit_happy_feedback_page()
        submit_happy_feedback_pg.type_feedback(u'It made my \u2603 come alive!')
        thanks_pg = submit_happy_feedback_pg.submit_feedback()
        Assert.true(thanks_pg.is_the_current_page)

    @pytest.mark.xfail(reason='Functionality missing - remaining characters count')
    @pytest.mark.nondestructive
    def test_remaining_character_count(self, mozwebqa):
        """This testcase covers # 13806 in Litmus.

        1. Verifies the remaining character count decreases
        2. Verifies that the remaining character count style changes at certain thresholds
        3. Verified that the 'Submit Feedback' button is disabled when character limit is exceeded

        """
        from pages.desktop.submit_happy_feedback import SubmitHappyFeedbackPage
        submit_happy_feedback_pg = SubmitHappyFeedbackPage(mozwebqa)

        submit_happy_feedback_pg.go_to_submit_happy_feedback_page()
        Assert.equal(submit_happy_feedback_pg.remaining_character_count, 250)
        Assert.false(submit_happy_feedback_pg.is_remaining_character_count_limited)
        Assert.false(submit_happy_feedback_pg.is_remaining_character_count_negative)
        Assert.false(submit_happy_feedback_pg.is_submit_feedback_enabled)

        submit_happy_feedback_pg.type_feedback("a" * 199)
        Assert.equal(submit_happy_feedback_pg.remaining_character_count, 51)
        Assert.false(submit_happy_feedback_pg.is_remaining_character_count_limited)
        Assert.false(submit_happy_feedback_pg.is_remaining_character_count_negative)
        Assert.true(submit_happy_feedback_pg.is_submit_feedback_enabled)

        submit_happy_feedback_pg.type_feedback("b")
        Assert.equal(submit_happy_feedback_pg.remaining_character_count, 50)
        Assert.true(submit_happy_feedback_pg.is_remaining_character_count_limited)
        Assert.false(submit_happy_feedback_pg.is_remaining_character_count_negative)
        Assert.true(submit_happy_feedback_pg.is_submit_feedback_enabled)

        submit_happy_feedback_pg.type_feedback("c" * 50)
        Assert.equal(submit_happy_feedback_pg.remaining_character_count, 0)
        Assert.true(submit_happy_feedback_pg.is_remaining_character_count_limited)
        Assert.false(submit_happy_feedback_pg.is_remaining_character_count_negative)
        Assert.true(submit_happy_feedback_pg.is_submit_feedback_enabled)

        submit_happy_feedback_pg.type_feedback("d")
        Assert.equal(submit_happy_feedback_pg.remaining_character_count, -1)
        Assert.false(submit_happy_feedback_pg.is_remaining_character_count_limited)
        Assert.true(submit_happy_feedback_pg.is_remaining_character_count_negative)
        Assert.false(submit_happy_feedback_pg.is_submit_feedback_enabled)

    @pytest.mark.nondestructive
    def test_navigating_away_from_initial_submit_feedback_page(self, mozwebqa):
        """Litmus 13651 - Input: Submit feedback page."""
        from pages.desktop.submit_feedback import SubmitFeedbackPage
        submit_feedback_pg = SubmitFeedbackPage(mozwebqa)
        submit_feedback_pg.go_to_submit_feedback_page()

        happy_feedback_pg = submit_feedback_pg.click_happy_feedback()
        Assert.equal(happy_feedback_pg.current_page_url, "%s/en-US/feedback/#happy" % mozwebqa.base_url)
        happy_feedback_pg.click_back()

        sad_feedback_pg = submit_feedback_pg.click_sad_feedback()
        Assert.equal(sad_feedback_pg.current_page_url, "%s/en-US/feedback/#sad" % mozwebqa.base_url)
        sad_feedback_pg.click_back()

        Assert.equal(submit_feedback_pg.support_page_link_address, 'http://support.mozilla.org/')
