from fjord.base.templatetags.jinja_helpers import locale_name, urlparams
from fjord.base.tests import TestCase


class TestLocaleName(TestCase):
    def test_english(self):
        data = [
            (u'en-US', u'English (US)'),
            (u'es', u'Spanish'),
            (u'gd', u'Gaelic (Scotland)'),
            (u'xx', u'Unknown')
        ]
        for name, expected in data:
            assert unicode(locale_name(name)) == expected

    def test_native(self):
        data = [
            (u'en-US', u'English (US)'),
            (u'es', u'Espa\u00f1ol'),
            (u'gd', u'G\u00e0idhlig'),
            (u'xx', u'Unknown')
        ]
        for name, expected in data:
            assert unicode(locale_name(name, native=True)) == expected


class TestUrlParams(TestCase):
    def test_utf8_urlencoded_query(self):
        """urlparams should not modify urlencoded unicode."""
        # %C3%B1 is urlencoded unicode.
        url = u'http://example.com/foo.html?bar=%C3%B1'
        assert urlparams(url, hash='biff') == url + u'#biff'
