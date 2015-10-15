from fjord.base.tests import TestCase
from fjord.feedback.utils import clean_url


class TestCleanUrl(TestCase):
    def test_basic(self):
        data = [
            (None, None),
            ('', ''),
            ('http://example.com/', 'http://example.com/'),
            ('http://example.com/#foo', 'http://example.com/'),
            ('http://example.com/?foo=bar', 'http://example.com/'),
            ('http://example.com:8000/', 'http://example.com/'),
            ('ftp://foo.bar/', ''),
            ('chrome://something', 'chrome://something'),
            ('about:home', 'about:home'),
        ]

        for url, expected in data:
            assert clean_url(url) == expected
