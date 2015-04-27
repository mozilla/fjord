# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from unittestzero import Assert


from tests import TestCase
from pages.dashboard import DashboardPage
from pages.fxos_feedback_form import FxOSFeedbackFormPage


class TestFeedback(TestCase):
    def test_submit_happy_feedback(self, mozwebqa):
        timestamp = str(time.time())
        desc = 'input-tests testing happy fxos feedback ' + timestamp

        # 1. go to the feedback form
        feedback_pg = FxOSFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. pick default country
        feedback_pg.click_country_next()

        # 4. pick default device
        feedback_pg.click_device_next()

        # 5. fill in description
        Assert.false(feedback_pg.is_submit_enabled)
        feedback_pg.set_description(desc)
        Assert.true(feedback_pg.is_submit_enabled)

        # 6. fill in url
        # FIXME: set url

        # 7. fill in email address
        # FIXME: check email input disabled
        feedback_pg.check_email_checkbox()
        # FIXME: check email input enabled
        feedback_pg.set_email('foo@example.com')

        # 8. submit
        feedback_pg.submit(expect_success=True)
        self.take_a_breather()
        Assert.equal(feedback_pg.current_card, 'thanks')

        # 9. verify
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        Assert.equal(resp.type.strip(), 'Happy')
        Assert.equal(resp.body.strip(), desc.strip())
        Assert.equal(resp.locale.strip(), 'English (US)')
        # FIXME: test email (can't because it's hidden when not authenticated)
        # FIXME: test url (can't because it's hidden when not authenticated)

    def test_submit_sad_feedback(self, mozwebqa):
        timestamp = str(time.time())
        desc = 'input-tests testing sad fxos feedback ' + timestamp

        # 1. go to the feedback form
        feedback_pg = FxOSFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page()

        # 2. click on happy
        feedback_pg.click_sad_feedback()

        # 3. pick default country
        feedback_pg.click_country_next()

        # 4. pick default device
        feedback_pg.click_device_next()

        # 5. fill in description
        feedback_pg.set_description(desc)

        # 6. submit
        feedback_pg.submit(expect_success=True)
        self.take_a_breather()
        Assert.equal(feedback_pg.current_card, 'thanks')

        # 7. verify
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        Assert.equal(resp.type.strip(), 'Sad')
        Assert.equal(resp.body.strip(), desc.strip())
        Assert.equal(resp.locale.strip(), 'English (US)')

    # FIXME: Test back and forth

    # FIXME: Test happy submit with unicode

    # FIXME: Test character counter

    # FIXME: Test email verification
