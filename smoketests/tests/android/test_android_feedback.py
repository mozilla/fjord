# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import pytest
from tests import TestCase
from pages.dashboard import DashboardPage
from pages.android_feedback_form import AndroidFeedbackFormPage


class TestFeedback(TestCase):

    @pytest.mark.nondestructive
    def test_on_device_links(self, mozwebqa):
        feedback_pg = AndroidFeedbackFormPage(mozwebqa)
        version = "44"
        channel = "beta"
        last_url = "http://mozilla.com"
        on_device = True

        # Go to feedback page on device, look for links
        feedback_pg.go_to_feedback_page(version, channel, last_url, on_device)
        assert feedback_pg.on_device_links_present

    @pytest.mark.nondestructive
    def test_on_desktop_links(self, mozwebqa):
        feedback_pg = AndroidFeedbackFormPage(mozwebqa)
        version = "44"
        channel = "beta"
        last_url = "http://mozilla.com"
        on_device = False

        # Go to feedback page on desktop, look for links
        feedback_pg.go_to_feedback_page(version, channel, last_url, on_device)
        assert feedback_pg.on_device_links_present is False

    @pytest.mark.nondestructive
    def test_submit_happy_feedback(self, mozwebqa):
        feedback_pg = AndroidFeedbackFormPage(mozwebqa)
        version = "44"
        channel = "beta"
        last_url = "http://mozilla.com"
        on_device = True

        # Go to feedback page and click happy
        feedback_pg.go_to_feedback_page(version, channel, last_url, on_device)
        feedback_pg.click_happy_feedback()
        assert feedback_pg.current_sentiment == 'happy'

    @pytest.mark.nondestructive
    def test_submit_happy_feedback_in_beta(self, mozwebqa):
        feedback_pg = AndroidFeedbackFormPage(mozwebqa)
        version = "44"
        channel = "beta"
        last_url = "http://mozilla.com"
        on_device = True

        # Go to happy page in beta, on device
        feedback_pg.go_to_feedback_page(version, channel, last_url, on_device)
        feedback_pg.click_happy_feedback()
        assert feedback_pg.playstore_link_is_intent_beta

    @pytest.mark.nondestructive
    def test_submit_happy_feedback_in_release_on_device(self, mozwebqa):
        feedback_pg = AndroidFeedbackFormPage(mozwebqa)
        version = "44"
        channel = "release"
        last_url = "http://mozilla.com"
        on_device = True

        # Go to happy page in release channel, on device
        feedback_pg.go_to_feedback_page(version, channel, last_url, on_device)
        feedback_pg.click_happy_feedback()
        assert feedback_pg.playstore_link_is_intent_release

    @pytest.mark.nondestructive
    def test_submit_happy_feedback_in_release_on_desktop(self, mozwebqa):
        feedback_pg = AndroidFeedbackFormPage(mozwebqa)
        version = "44"
        channel = "release"
        last_url = "http://mozilla.com"
        on_device = False

        # Go to happy page in release channel, on desktop
        feedback_pg.go_to_feedback_page(version, channel, last_url, on_device)
        feedback_pg.click_happy_feedback()
        assert feedback_pg.playstore_link_is_http_release

    def test_submit_sad_feedback(self, mozwebqa):
        feedback_pg = AndroidFeedbackFormPage(mozwebqa)
        timestamp = str(time.time())
        desc = 'input-tests testing sad android feedback ' + timestamp
        version = "44"
        channel = "beta"
        last_url = "http://mozilla.com"
        on_device = True

        # 1. Go to feedback page and click sad
        feedback_pg.go_to_feedback_page(version, channel, last_url, on_device)
        feedback_pg.click_sad_feedback()
        assert feedback_pg.current_sentiment == 'sad'

        # 2. Look for Support link
        assert feedback_pg.support_link_present

        # 3. Look for URL we passed
        assert feedback_pg.url_prepopulated() == last_url

        # 4. don't send the URL
        feedback_pg.uncheck_url()

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
        # we didn't send the url, it should not be here
        assert resp.site.strip() != last_url
