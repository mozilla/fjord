from nose.tools import eq_

from fjord.base.helpers import locale_name
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
