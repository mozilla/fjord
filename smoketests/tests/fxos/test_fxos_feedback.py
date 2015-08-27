# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

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

        # Verify there is a privacy link
        feedback_pg.has_privacy_link

        # 2. click on happy
        feedback_pg.click_happy_feedback()

        # 3. pick default country
        feedback_pg.click_country_next()

        # 4. pick default device
        feedback_pg.click_device_next()

        # 5. fill in description
        feedback_pg.has_privacy_link
        assert feedback_pg.is_submit_enabled is False
        feedback_pg.set_description(desc)
        assert feedback_pg.is_submit_enabled is True

        # 6. fill in url
        feedback_pg.set_url('http://example.com/foo')

        # 7. fill in email address
        # FIXME: check email input disabled
        feedback_pg.check_email_checkbox()
        # FIXME: check email input enabled
        feedback_pg.set_email('foo@example.com')

        # 8. submit
        feedback_pg.submit(expect_success=True)
        self.take_a_breather()
        assert feedback_pg.current_card == 'thanks'

        # 9. verify
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        assert resp.type.strip() == 'Happy'
        assert resp.body.strip() == desc.strip()
        assert resp.locale.strip() == 'English (US)'
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
        assert feedback_pg.current_card == 'thanks'

        # 7. verify
        dashboard_pg = DashboardPage(mozwebqa)
        dashboard_pg.go_to_dashboard_page()
        dashboard_pg.search_for(desc)
        resp = dashboard_pg.messages[0]
        assert resp.type.strip() == 'Sad'
        assert resp.body.strip() == desc.strip()
        assert resp.locale.strip() == 'English (US)'

    # FIXME: Test back and forth

    # FIXME: Test happy submit with unicode

    # FIXME: Test character counter

    # FIXME: Test email verification
