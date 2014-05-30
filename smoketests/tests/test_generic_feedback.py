#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from nose.tools import eq_, ok_

from . import BaseTestCase, nondestructive


class TestFeedback(BaseTestCase):

    def test_submit_happy_feedback(self, mozwebqa):
        """Fill out happy feedback"""
        timestamp = str(time.time())
        desc = 'input-tests testing happy feedback ' + timestamp
        url = 'http://happy.example.com/' + timestamp

        # 1. go to the feedback form
        from pages.desktop.generic_feedback_form import GenericFeedbackFormPage
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. fill out description and url
        feedback_pg.set_description(desc)
        feedback_pg.set_url(url)
        feedback_pg.click_moreinfo_next()

        # 4. fill in email address
        feedback_pg.check_email_checkbox()
        feedback_pg.set_email('foo@example.com')

        # 5. submit
        thanks_pg = feedback_pg.submit(expect_success=True)
        ok_(thanks_pg.is_the_current_page)

        # 6. verify
        from pages.desktop.feedback import FeedbackPage
        dashboard_pg = FeedbackPage(mozwebqa)
        dashboard_pg.go_to_feedback_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        eq_(resp.type.strip(), 'Happy')
        eq_(resp.body.strip(), desc.strip())
        eq_(resp.locale.strip(), 'English (US)')
        eq_(resp.site.strip(), 'example.com')

    def test_submit_sad_feedback(self, mozwebqa):
        """Fill out sad feedback"""
        timestamp = str(time.time())
        desc = 'input-tests testing sad feedback ' + timestamp
        url = 'http://sad.example.com/' + timestamp

        # 1. go to the feedback form
        from pages.desktop.generic_feedback_form import GenericFeedbackFormPage
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        # 2. click on sad
        feedback_pg.click_sad_feedback()

        # 3. fill out description and url
        feedback_pg.set_description(desc)
        feedback_pg.set_url(url)
        feedback_pg.click_moreinfo_next()

        # 4. fill in email address
        feedback_pg.check_email_checkbox()
        feedback_pg.set_email('foo@example.com')

        # 5. submit
        thanks_pg = feedback_pg.submit(expect_success=True)
        ok_(thanks_pg.is_the_current_page)

        # 6. verify
        from pages.desktop.feedback import FeedbackPage
        dashboard_pg = FeedbackPage(mozwebqa)
        dashboard_pg.go_to_feedback_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        eq_(resp.type.strip(), 'Sad')
        eq_(resp.body.strip(), desc.strip())
        eq_(resp.locale.strip(), 'English (US)')
        eq_(resp.site.strip(), 'example.com')

    @nondestructive
    def test_back_and_forth(self, mozwebqa):
        """Test next and back buttons"""
        desc = 'input-tests testing'

        # 1. go to the feedback form
        from pages.desktop.generic_feedback_form import GenericFeedbackFormPage
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. click back and happy again
        feedback_pg.click_moreinfo_back()
        feedback_pg.click_happy_feedback()

        # 4. check next button is disabled, fill out description,
        # check next button is enabled and move on
        ok_(not feedback_pg.is_moreinfo_next_enabled)
        feedback_pg.set_description(desc)
        ok_(feedback_pg.is_moreinfo_next_enabled)
        feedback_pg.click_moreinfo_next()

        # 5. click back and next again
        feedback_pg.click_email_back()
        feedback_pg.click_moreinfo_next()

    def test_submitting_same_feedback_twice(self, mozwebqa):
        """Submitting the same feedback twice ignores the second"""
        desc = 'input-tests testing repeat feedback'

        # Submit the feedback the first time
        from pages.desktop.generic_feedback_form import GenericFeedbackFormPage
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()
        feedback_pg.click_happy_feedback()
        feedback_pg.set_description(desc)
        feedback_pg.click_moreinfo_next()
        thanks_pg = feedback_pg.submit(expect_success=True)
        ok_(thanks_pg.is_the_current_page)

        from pages.desktop.feedback import FeedbackPage
        dashboard_pg = FeedbackPage(mozwebqa)
        dashboard_pg.go_to_feedback_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        eq_(resp.body.strip(), desc.strip())
        first_id = resp.response_id.strip()

        # Submit it a second time--we get the Thank You page again and
        # it looks identical to the first time.
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()
        feedback_pg.click_happy_feedback()
        feedback_pg.set_description(desc)
        feedback_pg.click_moreinfo_next()
        thanks_pg = feedback_pg.submit(expect_success=True)
        ok_(thanks_pg.is_the_current_page)

        # Check the dashboard again and make sure the most recent
        # response has the same created time as the first time. If it
        # does, then
        dashboard_pg = FeedbackPage(mozwebqa)
        dashboard_pg.go_to_feedback_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        eq_(resp.body.strip(), desc.strip())
        second_id = resp.response_id.strip()

        # The two ids should be the same because the second response
        # didn't go through.
        eq_(first_id, second_id)

    def test_submit_happy_feedback_with_unicode(self, mozwebqa):
        """Fill out happy feedback with unicode description"""
        timestamp = str(time.time())
        desc = u'input-tests testing happy feedback with unicode \u2603 ' + timestamp

        # 1. go to the feedback form
        from pages.desktop.generic_feedback_form import GenericFeedbackFormPage
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. fill out description and url
        feedback_pg.set_description(desc)
        feedback_pg.click_moreinfo_next()

        # 4. submit
        thanks_pg = feedback_pg.submit(expect_success=True)
        ok_(thanks_pg.is_the_current_page)

        # 5. verify
        from pages.desktop.feedback import FeedbackPage
        dashboard_pg = FeedbackPage(mozwebqa)
        dashboard_pg.go_to_feedback_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        eq_(resp.type.strip(), 'Happy')
        eq_(resp.body.strip(), desc.strip())

    @nondestructive
    def test_remaining_character_count(self, mozwebqa):
        from pages.desktop.generic_feedback_form import GenericFeedbackFormPage
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        feedback_pg.click_happy_feedback()

        eq_(feedback_pg.remaining_character_count, 10000)

        feedback_pg.set_description('aaaaa')
        eq_(feedback_pg.remaining_character_count, 9995)

        feedback_pg.set_description('a' * 100)
        eq_(feedback_pg.remaining_character_count, 9895)

        # Doing setvalue clears the text, so we do that for 9998 of
        # them and then add one more for 9999.
        feedback_pg.set_description('a' * 9998, send_keys=False)
        feedback_pg.set_description('a')
        eq_(feedback_pg.remaining_character_count, 1)

        feedback_pg.set_description('a')
        eq_(feedback_pg.remaining_character_count, 0)

        feedback_pg.set_description('a')
        eq_(feedback_pg.remaining_character_count, -1)

    @nondestructive
    def test_url_verification(self, mozwebqa):
        from pages.desktop.generic_feedback_form import GenericFeedbackFormPage
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        feedback_pg.click_happy_feedback()
        feedback_pg.set_description('ou812')

        valid = [
            '',
            'example.com',
            'ftp://example.com',
            'http://example.com',
            'https://example.com',
            'https://foo.example.com:8000/blah/blah/?foo=bar#baz',
            u'http://mozilla.org/\u2713'
        ]
        for url in valid:
            feedback_pg.set_url(url)
            ok_(feedback_pg.is_url_valid)

        invalid = [
            'a',
            'about:start',
            'chrome://somepage',
            'http://example'
        ]
        for url in invalid:
            feedback_pg.set_url(url)
            ok_(not feedback_pg.is_url_valid)

    @nondestructive
    def test_email_verification(self, mozwebqa):
        from pages.desktop.generic_feedback_form import GenericFeedbackFormPage
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        feedback_pg.click_happy_feedback()
        feedback_pg.set_description('ou812')
        feedback_pg.click_moreinfo_next()

        feedback_pg.check_email_checkbox()

        valid = [
            '',
            'foo@example.com',
            'foo@bar.example.com',
            'foo@a.com'
        ]
        for email in valid:
            feedback_pg.set_email(email)
            ok_(feedback_pg.is_email_valid)

        invalid = [
            'foo@',
            'foo@example',
        ]
        for email in invalid:
            feedback_pg.set_email(email)
            ok_(not feedback_pg.is_email_valid)
