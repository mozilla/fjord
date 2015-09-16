#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.base import Page


class QunitPage(Page):
    _qunit_test_result = (By.CSS_SELECTOR, '#qunit-testresult')
    _qunit_test_groups = (By.CSS_SELECTOR, '#qunit-tests > li.pass, #qunit-tests > li.fail')

    def go_to_qunit_page(self):
        self.selenium.get(self.base_url + '/static/tests/index.html')

    def wait_for_completion(self):
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element(self._qunit_test_result, 'Tests completed')
        )

    def check_all_passed(self):
        # Get test results.
        test_groups = self.selenium.find_elements(*self._qunit_test_groups)
        total_fails = 0

        # Print number of test groups so it's more likely we notice problems
        # with this test.
        print 'QUNIT: examining %d test groups...' % len(test_groups)

        # Go through each test group to see status.
        for group in test_groups:
            state = group.get_attribute('class')

            # If the whole group passed, we don't need to check
            # individual tests, so we can move on.
            if state == 'pass':
                print 'QUNIT GROUP PASS'
                continue

            # Suite didn't pass, so we check individual tests in the group and
            # print out a message for each failure.
            total_fails += 1
            title = group.find_element(By.CSS_SELECTOR, '.test-name').text
            tests = group.find_elements(By.CSS_SELECTOR, '.pass, .fail')
            for test_elem in tests:
                state = test_elem.get_attribute('class')
                if state == 'pass':
                    print 'QUNIT PASS: %s' % title
                    continue

                expects = test_elem.find_elements(By.CSS_SELECTOR, '.test-expected pre')
                actuals = test_elem.find_elements(By.CSS_SELECTOR, '.test-actual pre')

                actual = actuals[0].text if len(actuals) else None
                expect = expects[0].text if len(expects) else None

                print 'QUNIT FAIL: in "%s": %s != %s' % (title, expect, actual)

        return total_fails == 0
