from fjord.base.tests import TestCase
from fjord.feedback.tests import ProductFactory, ResponseFactory
from fjord.suggest.providers.trigger.models import _generate_keywords_regex
from fjord.suggest.providers.trigger.tests import TriggerRuleFactory


class TriggerRuleMatchTests(TestCase):
    def test_match_locale(self):
        tests = [
            # tr locales, feedback locale, expected
            ([], '', True),
            ([], 'en-US', True),
            ([], 'fr', True),

            (['en-US'], '', False),
            (['en-US'], 'en-US', True),
            (['en-US'], 'fr', False),

            (['en-US', 'fr'], '', False),
            (['en-US', 'fr'], 'en-US', True),
            (['en-US', 'fr'], 'fr', True),
            (['en-US', 'fr'], 'es', False)
        ]
        for tr_locales, feedback_locale, expected in tests:
            tr = TriggerRuleFactory(locales=tr_locales)
            assert tr.match_locale(feedback_locale) == expected

    def test_match_versions(self):
        tests = [
            # tr versions, feedback version, expected
            ([], '', True),
            ([], '38', True),
            ([], '38.0.5', True),

            (['38'], '', False),
            (['38'], '38', True),
            (['38'], '38.0.5', False),

            (['38*'], '', False),
            (['38*'], '38', True),
            (['38*'], '38.0.5', True),

            (['38*', '37.1'], '', False),
            (['38*', '37.1'], '38', True),
            (['38*', '37.1'], '38.0.5', True),
            (['38*', '37.1'], '37', False),
            (['38*', '37.1'], '37.1', True)
        ]
        for tr_versions, feedback_version, expected in tests:
            tr = TriggerRuleFactory(versions=tr_versions)
            assert tr.match_version(feedback_version) == expected

    def test_match_product(self):
        # Test match all products
        tr = TriggerRuleFactory()

        assert tr.match_product('') is True
        assert tr.match_product('sprocket') is True

        # Test match specific product
        prod = ProductFactory()
        tr = TriggerRuleFactory()
        tr.products.add(prod)

        assert tr.match_product('') is False
        assert tr.match_product('sprocket') is False
        assert tr.match_product(prod.db_name) is True

    def test_match_keywords(self):
        tests = [
            # tr.keywords, description, expected
            ([], u'', True),
            ([], u'my dog has fleas', True),
            ([u'my'], u'', False),
            ([u'my'], u'my dog has fleas', True),
            ([u'my'], u'MY DOG HAS FLEAS', True),
            ([u'your', u'dog'], u'my dog has fleas', True),
            ([u'my dog'], u'my dog has fleas', True),
            ([u'my dog'], u'your dog has fleas', False),
            ([u'my dog', u'cat'], u'my dog has fleas', True),
            ([u'my cat'], u'my dog has fleas', False),
            ([u'my cat'], u'my  cat  hat  fleas', True),
            ([u'my  cat'], u'my  cat  hat  fleas', True),
            ([u'\xca'], u'abcd \xca abcd', True),
            ([u'my-cat'], u'my-cat has fleas', True),
            ([u'(my cat)'], u'(my cat) has fleas', True),
            ([u'cat'], u'i love my cat!', True),
            ([u'cat'], u'(cat)', True),
        ]
        for tr_keywords, description, expected in tests:
            tr = TriggerRuleFactory(keywords=tr_keywords)
            assert tr.match_description(description) == expected

    def test_match_url_exists(self):
        tests = [
            # tr.url_exists, url, expected
            (None, '', True),
            (None, 'https://example.com/', True),
            (True, '', False),
            (True, 'https://example.com/', True),
            (False, '', True),
            (False, 'https://example.com/', False)
        ]
        for tr_url_exists, url, expected in tests:
            tr = TriggerRuleFactory(url_exists=tr_url_exists)
            assert tr.match_url_exists(url) == expected

    def test_match(self):
        # Note: This isn't an exhaustive test. Just a rough cursory check.

        # TriggerRule that matches everything matches everything.
        tr = TriggerRuleFactory(
            versions=[],
            locales=[],
            keywords=[],
            products=[],
        )

        resp = ResponseFactory()
        assert tr.match(resp) is True

        tr = TriggerRuleFactory(
            versions=[u'38*'],
            locales=[u'en-US', u'fr'],
            keywords=[u'rc4'],
            url_exists=True
        )
        prod = ProductFactory()
        tr.products.add(prod)
        resp = ResponseFactory(
            version=u'38.0.5',
            locale=u'en-US',
            product=prod.db_name,
            description=u'rc4 is awesome',
            url=u'https://example.com/'
        )
        assert tr.match(resp) is True
        resp.locale = 'es'
        assert tr.match(resp) is False

    def test_keyword_regexes_are_cached(self):
        for text in [u'cat', u'dog', u'mouse']:
            tr = TriggerRuleFactory(keywords=[text])
            tr.match_description(text)

            tr = TriggerRuleFactory(keywords=[text])
            tr.match_description(text)

        cache_info = _generate_keywords_regex.cache_info()
        assert cache_info.hits >= 3
