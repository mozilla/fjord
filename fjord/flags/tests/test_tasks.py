from mock import patch
from nose.tools import eq_

# These tests require that tasks be imported so that the post_save
# signal is connected. Don't remove this.
import fjord.flags.tasks  # noqa

from fjord.base.tests import TestCase
from fjord.feedback.tests import ResponseFactory
from fjord.flags.spicedham_utils import get_spicedham, tokenize


class TestClassifyTask(TestCase):
    def test_classify_task(self):
        """flags should be created if classifier returns True"""
        with patch('fjord.flags.tasks.classify') as classify_mock:
            classify_mock.return_value = True

            # This creates the response and saves it which kicks off
            # the classifier task. It should be classified as abuse.
            resp1 = ResponseFactory(locale=u'en-US', description=u'ou812')

            eq_(classify_mock.call_count, 1)
            eq_(sorted([f.name for f in resp1.flag_set.all()]),
                ['abuse'])

    def test_classify_false_task(self):
        """flags shouldn't be created if classifier returns False"""
        with patch('fjord.flags.tasks.classify') as classify_mock:
            classify_mock.return_value = False

            # This creates the response and saves it which kicks off
            # the classifier task. It should not be classified as
            # abuse.
            resp1 = ResponseFactory(locale=u'en-US', description=u'ou812')

            eq_(classify_mock.call_count, 1)
            eq_([f.name for f in resp1.flag_set.all()], [])

    def test_ignore_non_english(self):
        """non-en-US responses should be ignored"""
        with patch('fjord.flags.tasks.classify') as classify_mock:
            # This response is not en-US, so classify should never get
            # called.
            resp1 = ResponseFactory(locale=u'es', description=u'ou812')

            eq_(classify_mock.called, False)
            eq_([f.name for f in resp1.flag_set.all()], [])


class TestClassification(TestCase):
    def train(self, descriptions, is_abuse=True):
        # Note: This is probably a cached Spicedham object.
        sham = get_spicedham()
        for desc in descriptions:
            sham.train(tokenize(desc), match=is_abuse)

    def test_abuse(self):
        self.train([
            'gross gross is gross gross gross browser',
            'gross icky gross gross browser',
            'gross is mcgrossy gross',
            'omg worst gross',
            'browser worst'
        ], is_abuse=True)

        self.train([
            'Firefox is super!',
            'Great browser!',
            'Super fast!',
            'Not gross!',
            'super not gross!'
        ], is_abuse=False)

        # This creates the response and saves it which kicks off
        # the classifier task. It should be classified as abuse.
        resp = ResponseFactory(
            locale=u'en-US', description=u'browser is gross!')

        eq_(sorted([f.name for f in resp.flag_set.all()]),
            ['abuse'])
