# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from unittestzero import Assert

from pages.dashboard import DashboardPage
from pages.generic_feedback_form import GenericFeedbackFormPage


class TestSubmit(object):
    def test_submit_happy_feedback(self, mozwebqa):
        timestamp = str(time.time())
        desc = 'input-tests testing happy feedback ' + timestamp
        url = 'http://happy.example.com/' + timestamp

        # 1. go to the feedback form
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')

        # Verify there is a privacy link
        feedback_pg.has_privacy_link

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. fill out description, url, email checkbox and email
        # address
        feedback_pg.has_privacy_link
        feedback_pg.set_description(desc)
        feedback_pg.set_url(url)
        feedback_pg.check_email_checkbox()
        feedback_pg.set_email('foo@example.com')

        # 4. submit
        thanks_pg = feedback_pg.submit(expect_success=True)
        Assert.true(thanks_pg.is_the_current_page)

        # 5. verify
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        Assert.equal(resp.type.strip(), 'Happy')
        Assert.equal(resp.body.strip(), desc.strip())
        Assert.equal(resp.locale.strip(), 'English (US)')
        Assert.equal(resp.site.strip(), 'example.com')

    def test_submit_sad_feedback(self, mozwebqa):
        timestamp = str(time.time())
        desc = 'input-tests testing sad feedback ' + timestamp
        url = 'http://sad.example.com/' + timestamp

        # 1. go to the feedback form
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')

        # 2. click on sad
        feedback_pg.click_sad_feedback()

        # 3. fill out description, url, email checkbox and email
        # address
        feedback_pg.set_description(desc)
        feedback_pg.set_url(url)
        feedback_pg.check_email_checkbox()
        feedback_pg.set_email('foo@example.com')

        # 4. submit
        thanks_pg = feedback_pg.submit(expect_success=True)
        Assert.true(thanks_pg.is_the_current_page)

        # 5. verify
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        Assert.equal(resp.type.strip(), 'Sad')
        Assert.equal(resp.body.strip(), desc.strip())
        Assert.equal(resp.locale.strip(), 'English (US)')
        Assert.equal(resp.site.strip(), 'example.com')

    def test_submit_sad_feedback_using_prefill(self, mozwebqa):
        timestamp = str(time.time())
        desc = 'input-tests testing sad feedback ' + timestamp

        # 1. go to the feedback form with sad prefill
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox', querystring='happy=0')

        # 2. fill out description
        feedback_pg.set_description(desc)

        # 3. submit
        thanks_pg = feedback_pg.submit(expect_success=True)
        Assert.true(thanks_pg.is_the_current_page)

        # 4. verify
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        Assert.equal(resp.type.strip(), 'Sad')
        Assert.equal(resp.body.strip(), desc.strip())
        Assert.equal(resp.locale.strip(), 'English (US)')

    def test_submitting_same_feedback_twice(self, mozwebqa):
        """Submitting the same feedback twice ignores the second"""
        timestamp = str(time.time())
        desc = 'input-tests testing repeat feedback ' + timestamp

        # Submit the feedback the first time
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')
        feedback_pg.click_happy_feedback()
        feedback_pg.set_description(desc)
        thanks_pg = feedback_pg.submit(expect_success=True)
        Assert.true(thanks_pg.is_the_current_page)

        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        Assert.equal(resp.body.strip(), desc.strip())
        first_id = resp.response_id.strip()

        # Submit it a second time--we get the Thank You page again and
        # it looks identical to the first time.
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')
        feedback_pg.click_happy_feedback()
        feedback_pg.set_description(desc)
        thanks_pg = feedback_pg.submit(expect_success=True)
        Assert.true(thanks_pg.is_the_current_page)

        # Check the dashboard again and make sure the most recent
        # response has the same created time as the first time. If it
        # does, then
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        Assert.equal(resp.body.strip(), desc.strip())
        second_id = resp.response_id.strip()

        # The two ids should be the same because the second response
        # didn't go through.
        Assert.equal(first_id, second_id)

    def test_submit_happy_feedback_with_unicode(self, mozwebqa):
        """Fill out happy feedback with unicode description"""
        timestamp = unicode(time.time())
        desc = u'input-tests testing happy feedback with unicode \u2603'
        desc = desc + u' ' + timestamp

        # 1. go to the feedback form
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. fill out description and url
        feedback_pg.set_description(desc)

        # 4. submit
        thanks_pg = feedback_pg.submit(expect_success=True)
        Assert.true(thanks_pg.is_the_current_page)

        # 5. verify
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        Assert.equal(resp.type.strip(), 'Happy')
        Assert.equal(resp.body.strip(), desc.strip())
