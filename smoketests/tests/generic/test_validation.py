# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from unittestzero import Assert

from pages.generic_feedback_form import GenericFeedbackFormPage
from tests import TestCase


class TestValidation(TestCase):
    @pytest.mark.nondestructive
    def test_remaining_character_count(self, mozwebqa):
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')

        feedback_pg.click_happy_feedback()

        Assert.equal(feedback_pg.remaining_character_count, 10000)

        feedback_pg.set_description('aaaaa')
        Assert.equal(feedback_pg.remaining_character_count, 9995)

        feedback_pg.update_description('a' * 100)
        Assert.equal(feedback_pg.remaining_character_count, 9895)

        # Doing setvalue clears the text, so we do that for 9998 of
        # them and then add one more for 9999.
        feedback_pg.set_description_execute_script('a' * 9998)
        # Update to kick off "input" event.
        feedback_pg.update_description('a')
        Assert.equal(feedback_pg.remaining_character_count, 1)

        feedback_pg.update_description('a')
        Assert.equal(feedback_pg.remaining_character_count, 0)

        feedback_pg.update_description('a')
        Assert.equal(feedback_pg.remaining_character_count, -1)

    @pytest.mark.nondestructive
    def test_url_verification(self, mozwebqa):
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')

        feedback_pg.click_happy_feedback()
        feedback_pg.set_description('ou812')

        valid = [
            '',
            'example.com',
            'ftp://example.com',
            'http://example.com',
            'https://example.com',
            'https://foo.example.com:8000/blah/blah/?foo=bar#baz',
            u'http://mozilla.org/\u2713',
            'about:config',
            'chrome://foo',
            '    example.com',
            'example.com    ',
            '    example.com    '
        ]
        for url in valid:
            feedback_pg.set_url(url)
            Assert.true(
                feedback_pg.is_url_valid,
                msg=('failed url "%s"' % url)
            )

        invalid = [
            'a',
            'http://example'
        ]
        for url in invalid:
            feedback_pg.set_url(url)
            Assert.false(
                feedback_pg.is_url_valid,
                msg=('failed url "%s"' % url)
            )

    @pytest.mark.nondestructive
    def test_email_verification(self, mozwebqa):
        feedback_pg = GenericFeedbackFormPage(mozwebqa)
        feedback_pg.go_to_feedback_page('firefox')

        feedback_pg.click_happy_feedback()
        feedback_pg.set_description('ou812')
        feedback_pg.check_email_checkbox()

        valid = [
            '',
            'foo@example.com',
            'foo@bar.example.com',
            'foo@a.com'
        ]
        for email in valid:
            feedback_pg.set_email(email)
            Assert.true(
                feedback_pg.is_email_valid,
                msg=('failed email "%s"' % email)
            )

        invalid = [
            'foo@',
            'foo@example',
        ]
        for email in invalid:
            feedback_pg.set_email(email)
            Assert.false(
                feedback_pg.is_email_valid,
                msg=('failed email "%s"' % email)
            )
