from fjord.base.tests import eq_, TestCase
from fjord.base.urlresolvers import reverse


class TestReverse(TestCase):
    def test_no_locale(self):
        # Note: This depends on the 'about' view. If we change that,
        # then it breaks this test. But it seems silly to do a bunch
        # of work to set up a better less fragile test plus it's
        # unlikely we'll change the 'about' view.
        eq_(reverse('about-view'), '/en-US/about')

    def test_locale(self):
        # Note: This depends on the 'about' view and the 'es'
        # locale. If we change those, then it breaks this test.
        eq_(reverse('about-view', locale='es'), '/es/about')
