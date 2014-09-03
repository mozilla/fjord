from nose.tools import eq_

from fjord.base.tests import TestCase

from fjord.feedback.tests import ResponseFactory
from fjord.flags.models import Flag
from fjord.flags.tests import FlagFactory


class TestFlagModel(TestCase):
    def test_flag(self):
        # Create a flag and a response, add the flag to the response
        # in a way we're probably going to use these things.
        FlagFactory(name='spam')
        resp = ResponseFactory()

        resp.flag_set.add(Flag.objects.get(name='spam'))

        eq_(resp.flag_set.count(), 1)
        eq_(Flag.objects.get(name='spam').responses.count(), 1)
