from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.feedback.tests import response


class TestResponseModel(TestCase):
    def test_description_truncate_on_save(self):
        # Extra 10 characters get lopped off on save.
        resp = response(description=('a' * 10010))
        resp.save()

        eq_(resp.description, 'a' * 10000)

    def test_description_strip_on_save(self):
        # Nix leading and trailing whitespace.
        resp = response(description=u'   \n\tou812\t\n   ')
        resp.save()

        eq_(resp.description, u'ou812')
