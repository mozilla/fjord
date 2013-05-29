from unittest import TestCase

from nose.tools import eq_

from fjord.analytics.tools import generate_query_parsed, to_tokens, unescape


class TestQueryParsed(TestCase):
    def test_to_tokens_good(self):
        eq_(to_tokens(u'abc'),
            [u'abc'])

        eq_(to_tokens(u'abc def'),
            [u'abc', u'def'])

        eq_(to_tokens(u'abc OR "def"'),
            [u'abc', u'OR', u'"def"'])

        eq_(to_tokens(u'abc OR "def ghi"'),
            [u'abc', u'OR', u'"def ghi"'])

        eq_(to_tokens(u'abc AND "def ghi"'),
            [u'abc', u'AND', u'"def ghi"'])

    def test_escaping(self):
        """Escaped things stay escaped"""
        tests = [
            (u'\\"AND', [u'\\"AND']),
            (u'\\"AND\\"', [u'\\"AND\\"']),
        ]
        for text, expected in tests:
            eq_(to_tokens(text), expected)

    def test_to_tokens_edge_cases(self):
        eq_(to_tokens(u'AND "def ghi'),
            [u'AND', u'"def ghi"'])

    def test_unescape(self):
        tests = [
            (u'foo', u'foo'),
            (u'\\foo', u'foo'),
            (u'\\\\foo', u'\\foo'),
            (u'foo\\', u'foo'),
            (u'foo\\\\', u'foo\\'),
            (u'foo\\bar', u'foobar'),
            (u'foo\\\\bar', u'foo\\bar'),
        ]
        for text, expected in tests:
            eq_(unescape(text), expected)

    def test_query_parsed(self):
        self.assertEqual(
            generate_query_parsed('foo', u'abc'),
            {'text': {'foo': u'abc'}})

        self.assertEqual(
            generate_query_parsed('foo', u'abc def'),
            {'text': {'foo': u'abc def'}},
        )

        self.assertEqual(
            generate_query_parsed('foo', u'abc "def" ghi'),
            {
                'bool': {
                    'minimum_should_match': 1,
                    'should': [
                        {'text': {'foo': u'abc'}},
                        {'text_phrase': {'foo': u'def'}},
                        {'text': {'foo': u'ghi'}},
                    ]
                }
            }
        )

        self.assertEqual(
            generate_query_parsed('foo', u'abc AND "def"'),
            {
                'bool': {
                    'must': [
                        {'text': {'foo': u'abc'}},
                        {'text_phrase': {'foo': u'def'}},
                    ]
                }
            }
        )

        self.assertEqual(
            generate_query_parsed('foo', u'abc OR "def" AND ghi'),
            {
                'bool': {
                    'minimum_should_match': 1,
                    'should': [
                        {'text': {'foo': u'abc'}},
                        {'bool': {
                                'must': [
                                    {'text_phrase': {'foo': u'def'}},
                                    {'text': {'foo': u'ghi'}},
                                ]
                        }}
                    ]
                }
            }
        )

        self.assertEqual(
            generate_query_parsed('foo', u'abc AND "def" OR ghi'),
            {
                'bool': {
                    'must': [
                        {'text': {'foo': u'abc'}},
                        {'bool': {
                                'minimum_should_match': 1,
                                'should': [
                                    {'text_phrase': {'foo': u'def'}},
                                    {'text': {'foo': u'ghi'}},
                                ]
                        }}
                    ]
                }
            }
        )

        self.assertEqual(
            generate_query_parsed('foo', u'14.1\\" screen'),
            {'text': {'foo': u'14.1" screen'}}
        )

    def test_query_parsed_edge_cases(self):
        self.assertEqual(
            generate_query_parsed('foo', u'AND "def'),
            {
                'bool': {
                    'must': [
                        {'text_phrase': {'foo': u'def'}}
                    ]
                }
            }
        )

        self.assertEqual(
            generate_query_parsed('foo', u'"def" AND'),
            {
                'bool': {
                    'must': [
                        {'text_phrase': {'foo': u'def'}}
                    ]
                }
            }
        )

        self.assertEqual(
            generate_query_parsed('foo', u'foo\\bar'),
            {'text': {'foo': u'foobar'}}
        )

        self.assertEqual(
            generate_query_parsed('foo', u'foo\\\\bar'),
            {'text': {'foo': u'foo\\bar'}}
        )
