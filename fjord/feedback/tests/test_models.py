from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.feedback.tests import response


class TestResponseModel(TestCase):
    def test_description_truncate_on_save(self):
        # Extra 10 characters get lopped off on save.
        resp = response(description=('a' * 10010))
        resp.save()

        eq_(resp.description, 'a' * 10000)
