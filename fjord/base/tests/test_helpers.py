from nose.tools import eq_

from fjord.base.helpers import locale_name, convert_date_string
from fjord.base.tests import TestCase


class TestLocaleName(TestCase):

    def test_english(self):
        eq_(locale_name('en-US'), u'English (US)')
        eq_(locale_name('es'), u'Spanish')
        eq_(locale_name('gd'), u'Gaelic (Scotland)')

    def test_native(self):
        eq_(locale_name('en-US', native=True), u'English (US)')
        eq_(locale_name('es', native=True), u'Espa\u00f1ol')
        eq_(locale_name('gd', native=True), u'G\u00e0idhlig')


class TestConvertDateString(TestCase):
    def test_bad_input(self):
        self.assertRaises(TypeError, lambda: convert_date_string(None))
        self.assertRaises(ValueError, lambda: convert_date_string(''))
        self.assertRaises(
            ValueError,
            lambda: convert_date_string('2013-04-03', in_fmt='%H:%M:%S'))

    def test_convert_date_string(self):
        eq_(convert_date_string('2013-04-03T14:42:15'), '2013-04-03')
        eq_(convert_date_string(u'2013-04-03T14:42:15'), '2013-04-03')

    def test_fmts(self):
        eq_(convert_date_string(u'2013-04-03', in_fmt='%Y-%m-%d'), '2013-04-03')
        eq_(convert_date_string(u'2013-04-03T14:42:15', out_fmt='%Y'), '2013')
