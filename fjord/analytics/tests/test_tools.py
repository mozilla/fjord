from datetime import datetime
from unittest import TestCase

from nose.tools import eq_

from fjord.analytics.tools import counts_to_options, zero_fill
from fjord.base.util import epoch_milliseconds


class TestCountsHelper(TestCase):
    def setUp(self):
        self.counts = [('apples', 5), ('bananas', 10), ('oranges', 6)]

    def test_basic(self):
        """Correct options should be set and values should be sorted.
        """
        options = counts_to_options(self.counts, 'fruit', 'Fruit')
        eq_(options['name'], 'fruit')
        eq_(options['display'], 'Fruit')

        eq_(options['options'][0], {
            'name': 'bananas',
            'display': 'bananas',
            'value': 'bananas',
            'count': 10,
            'checked': False,
        })
        eq_(options['options'][1], {
            'name': 'oranges',
            'display': 'oranges',
            'value': 'oranges',
            'count': 6,
            'checked': False,
        })
        eq_(options['options'][2], {
            'name': 'apples',
            'display': 'apples',
            'value': 'apples',
            'count': 5,
            'checked': False,
        })

    def test_map_dict(self):
        options = counts_to_options(self.counts, 'fruit', display_map={
            'apples': 'Apples',
            'bananas': 'Bananas',
            'oranges': 'Oranges',
        })
        # Note that options get sorted by count.
        eq_(options['options'][0]['display'], 'Bananas')
        eq_(options['options'][1]['display'], 'Oranges')
        eq_(options['options'][2]['display'], 'Apples')

    def test_map_func(self):
        options = counts_to_options(self.counts, 'fruit',
                                    value_map=lambda s: s.upper())
        # Note that options get sorted by count.
        eq_(options['options'][0]['value'], 'BANANAS')
        eq_(options['options'][1]['value'], 'ORANGES')
        eq_(options['options'][2]['value'], 'APPLES')

    def test_checked(self):
        options = counts_to_options(self.counts, 'fruit', checked='apples')
        # Note that options get sorted by count.
        assert not options['options'][0]['checked']
        assert not options['options'][1]['checked']
        assert options['options'][2]['checked']


class TestZeroFillHelper(TestCase):
    def test_zerofill(self):
        start = datetime(2012, 1, 1)
        end = datetime(2012, 1, 7)
        data1 = {
            epoch_milliseconds(datetime(2012, 1, 3)): 1,
            epoch_milliseconds(datetime(2012, 1, 5)): 1,
        }
        data2 = {
            epoch_milliseconds(datetime(2012, 1, 2)): 1,
            epoch_milliseconds(datetime(2012, 1, 5)): 1,
            epoch_milliseconds(datetime(2012, 1, 10)): 1,
        }
        zero_fill(start, end, [data1, data2])

        for day in range(1, 7):
            millis = epoch_milliseconds(datetime(2012, 1, day))
            assert millis in data1, "Day %s was not zero filled." % day
            assert millis in data2, "Day %s was not zero filled." % day
