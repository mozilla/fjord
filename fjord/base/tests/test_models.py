from django.core.exceptions import ValidationError

from fjord.base.models import ListField
from fjord.base.tests import TestCase


class ListFieldTestCase(TestCase):
    def test_to_python(self):
        tests = [
            # test data, expected
            (None, []),
            ([], []),
            ([1, 2, 3], [1, 2, 3]),
            (u'[1, 2, 3]', [1, 2, 3]),
            (u"[u'a', u'b', u'c']", [u'a', u'b', u'c'])
        ]
        field = ListField()
        for testcase, expected in tests:
            assert field.to_python(testcase) == expected

    def test_to_python_non_list_raises_validationerror_on_assert(self):
        field = ListField()
        self.assertRaises(ValidationError, field.to_python, (u'42',))

    def test_to_python_raises_validationerror_on_syntaxerror(self):
        field = ListField()
        self.assertRaises(ValidationError, field.to_python, (u'abc',))

    def test_get_prep_value(self):
        tests = [
            # test data, expected
            ([], u'[]'),
            ([1, 2], u'[1, 2]'),
            ([u'a', u'b'], u"[u'a', u'b']")
        ]
        field = ListField()
        for testcase, expected in tests:
            assert field.get_prep_value(testcase), expected
