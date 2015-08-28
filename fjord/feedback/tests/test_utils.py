from fjord.base.tests import TestCase
from fjord.feedback.utils import clean_url, compute_grams


class Testclean_url(TestCase):
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


class TestComputeGrams(TestCase):
    # FIXME - Beef this up so that we have more comprehensive tests of
    # the various tokenizing edge cases.

    def test_basic(self):
        test_data = [
            ('The quick brown fox', [u'brown quick', u'brown fox']),

            ('the latest update disables the New tab function',
             [u'disables new', u'function tab', u'new tab', u'latest update',
              u'disables update']),

            ('why is firefox so damn slow???? many tabs load slow or not at '
             'all!',
             [u'load tabs', u'load slow', u'slow tabs', u'damn slow']),

            ("I'm one of the guys that likes to try Firefox ahead of the "
             'herd... usually I use Nightly, but then a while back my '
             'favorite add-on, TabMixPlus stopped working because Firefox '
             "redid something in the code. \"No problem,\" says I to myself, "
             "I'll just use Aurora until they get it fixed.",
             [u'add-on favorite', u'add-on tabmixplus', u'ahead herd',
              u'ahead try', u'aurora fixed', u'aurora use', u'code problem',
              u'code redid', u'favorite nightly', u"guys i'm", u'guys likes',
              u'herd usually', u"i'll just", u"i'll myself", u'just use',
              u'likes try', u'myself says', u'nightly use', u'problem says',
              u'redid working', u'stopped tabmixplus', u'stopped working',
              u'use usually']),

            ('Being partially sighted, I found the features with Windows XP '
             'and IE8 extremely usefu;. I need everything in Arial black bold '
             'text.',
             [u'extremely usefu', u'features sighted', u'windows xp',
              u'ie8 xp', u'black bold', u'partially sighted', u'need usefu',
              u'features windows', u'arial need', u'arial black', u'bold text',
              u'extremely ie8']),
        ]

        for text, expected in test_data:
            assert sorted(compute_grams(text)) == sorted(expected)
