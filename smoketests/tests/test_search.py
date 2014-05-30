from unittestzero import Assert

from . import BaseTestCase, nondestructive
from pages.desktop.feedback import FeedbackPage


class TestSearch(BaseTestCase):

    @nondestructive
    def test_that_empty_search_of_feedback_returns_some_data(self, mozwebqa):
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        feedback_pg.search_for('')
        Assert.greater_equal(len(feedback_pg.messages), 1)

    @nondestructive
    def test_that_we_can_search_feedback_with_unicode(self, mozwebqa):
        feedback_pg = FeedbackPage(mozwebqa)

        feedback_pg.go_to_feedback_page()
        feedback_pg.search_for(u"p\xe1gina")
        # There's no way to guarantee that the search we did finds
        # responses on the page. So we check for one of two possible
        # scenarios: existences of responses or a message count of 0.
        Assert.true(
            (len(feedback_pg.messages) > 0)
            or feedback_pg.no_messages
        )
