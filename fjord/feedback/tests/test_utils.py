from contextlib import contextmanager

import pytest

from fjord.feedback.utils import clean_url, convert_emoji


class TestCleanUrl:
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


def unicodedata2_installed():
    try:
        import unicodedata2  # noqa
        return True
    except ImportError:
        return False


@contextmanager
def import_unicodedata():
    try:
        from fjord.feedback import utils
        old_unicodedata = utils.unicodedata
        import unicodedata
        utils.unicodedata = unicodedata

        yield

    finally:
        utils.unicodedata = old_unicodedata


class TestConvertEmoji:
    def test_no_emoji(self):
        assert convert_emoji(u'Example example') == 'Example example'

    def test_unicodedata(self):
        """Remove emoji if unicodedata2 is not installed"""
        with import_unicodedata():
            assert convert_emoji(u'Example \U0001f62a') == 'Example '

    @pytest.mark.skipif(not unicodedata2_installed(),
                        reason='unicodedata2 not installed')
    def test_sleepy_face(self):
        """Replace emoji with name if unicodedata2 is installed"""
        assert convert_emoji(u'Example \U0001f62a') == 'Example SLEEPY FACE'
