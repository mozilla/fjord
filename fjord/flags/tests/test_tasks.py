from mock import patch
from nose.tools import eq_

from fjord.base.tests import TestCase
from fjord.feedback.tests import ResponseFactory


class TestClassifyTask(TestCase):
    def test_classify_task(self):
        """flags should be created if classifier returns True"""
        with patch('fjord.flags.tasks.classify') as classify_mock:
            classify_mock.return_value = True

            # This creates the response and saves it which should kick off
            # the classifier and classify it as spam and abuse.
            resp1 = ResponseFactory(locale=u'en-US', description=u'ou812')

            eq_(classify_mock.call_count, 2)
            eq_(sorted([f.name for f in resp1.flag_set.all()]),
                ['abuse', 'spam'])

    def test_classify_false_task(self):
        """flags shouldn't be created if classifier returns False"""
        with patch('fjord.flags.tasks.classify') as classify_mock:
            classify_mock.return_value = False

            # This creates the response and saves it which should kick off
            # the classifier and classify it as spam and abuse.
            resp1 = ResponseFactory(locale=u'en-US', description=u'ou812')

            eq_(classify_mock.call_count, 2)
            eq_([f.name for f in resp1.flag_set.all()], [])

    def test_ignore_non_english(self):
        """non-en-US responses should be ignored"""
        with patch('fjord.flags.tasks.classify') as classify_mock:
            # This response is not en-US, so classify should never get
            # called.
            resp1 = ResponseFactory(locale=u'es', description=u'ou812')

            eq_(classify_mock.called, False)
            eq_([f.name for f in resp1.flag_set.all()], [])
