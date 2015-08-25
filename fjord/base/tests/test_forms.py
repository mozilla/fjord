from django.core.exceptions import ValidationError
from django.test import TestCase

from fjord.base.forms import EnhancedURLField, StringListField


class StringListTestCase(TestCase):
    def test_prepare_value(self):
        test_data = [
            # test data, expected
            ([], u''),
            ([u'a'], u'a'),
            ([u'a', u'b'], u'a\nb'),
        ]
        field = StringListField(required=False)
        for testcase, expected in test_data:
            assert field.prepare_value(testcase) == expected

    def test_clean(self):
        test_data = [
            # test data, expected
            (u'', []),
            (u'a', [u'a']),
            (u'a\nb', [u'a', u'b']),
            (u'  a  \n b\n\n', [u'a', u'b'])
        ]
        field = StringListField(required=False)
        for testcase, expected in test_data:
            assert field.clean(testcase) == expected


class EnhancedURLFieldTestCase(TestCase):
    def test_valid(self):
        test_data = [
            # expected, url
            ('about:mozilla', 'about:mozilla'),
            ('chrome://foo', 'chrome://foo'),
            ('ftp://example.com/', 'ftp://example.com'),

            # From Django's URLField test data
            ('http://localhost/', 'http://localhost'),
            ('http://example.com/', 'http://example.com'),
            ('http://example.com./', 'http://example.com.'),
            ('http://www.example.com/', 'http://www.example.com'),
            ('http://www.example.com:8000/test',
             'http://www.example.com:8000/test'),
            ('http://valid-with-hyphens.com/', 'valid-with-hyphens.com'),
            ('http://subdomain.domain.com/', 'subdomain.domain.com'),
            ('http://200.8.9.10/', 'http://200.8.9.10'),
            ('http://200.8.9.10:8000/test', 'http://200.8.9.10:8000/test'),
            ('http://valid-----hyphens.com/', 'http://valid-----hyphens.com'),
            ('http://www.example.com/s/http://code.djangoproject.com/tkt/13',
             'www.example.com/s/http://code.djangoproject.com/tkt/13'),
        ]

        f = EnhancedURLField()

        for expected, url in test_data:
            try:
                assert f.clean(url) == expected
            except ValidationError:
                print url
                raise

    def test_invalid(self):
        test_data = [
            # From Django's URLField test data
            ('This field is required.', ''),
            ('This field is required.', None),
            ('Enter a valid URL.', 'foo'),
            ('Enter a valid URL.', 'http://'),
            ('Enter a valid URL.', 'http://example'),
            ('Enter a valid URL.', 'http://example.'),
            ('Enter a valid URL.', 'com.'),
            ('Enter a valid URL.', '.'),
            ('Enter a valid URL.', 'http://.com'),
            ('Enter a valid URL.', 'http://invalid-.com'),
            ('Enter a valid URL.', 'http://-invalid.com'),
            ('Enter a valid URL.', 'http://inv-.alid-.com'),
            ('Enter a valid URL.', 'http://inv-.-alid.com'),
            ('Enter a valid URL.', '[a'),
            ('Enter a valid URL.', 'http://[a'),
        ]

        f = EnhancedURLField()

        for msg, url in test_data:
            try:
                f.clean(url)
            except ValidationError as exc:
                assert exc.messages == [msg]
