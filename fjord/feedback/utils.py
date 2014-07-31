from hashlib import md5
import re
import urlparse

from elasticsearch.exceptions import ElasticsearchException

from django.utils.encoding import force_str

from fjord.feedback import config
from fjord.search.index import es_analyze


TOKEN_SPLIT_RE = re.compile(r'[\s\.\,\/\\\?\;\:\"\*\&\^\%\$\#\@\!]+')


def tokenize(text):
    """Tokenizes the text

    1. lowercases text
    2. throws out all non-alpha-characters
    3. nixes all stop words

    """
    # Lowercase the text
    text = text.lower()

    # Nix all non-word characters
    tokens = TOKEN_SPLIT_RE.split(text)

    # Nix all stopwords and one-letter characters
    tokens = [token for token in tokens
              if (token not in config.ANALYSIS_STOPWORDS
                  and len(token) > 1)]

    # Return whatever we have left
    return tokens


def compute_grams(text):
    """Computes bigrams from analyzed text

    :arg text: text to analyze and generate bigrams from

    :returns: list of bigrams

    >>> compute_grams(u'The quick brown fox jumped')
    [u'quick brown', u'brown fox', u'fox jumped']

    """
    if not text:
        return []

    tokens = tokenize(text)

    # Generate set of bigrams. A bigram is a set of two consecutive
    # tokens. We put them in a set because we don't want duplicates.
    # We sort them so that "youtube crash" will match "crash youtube".
    bigrams = set()
    if len(tokens) >= 2:
        for i in range(len(tokens) - 1):
            bigrams.add(u' '.join(
                sorted([tokens[i], tokens[i+1]])))

    return list(bigrams)


def clean_url(url):
    """Takes a user-supplied url and cleans bits out

    This removes:

    1. nixes any non http/https/chrome/about urls
    2. port numbers
    3. query string variables
    4. hashes

    """
    if not url:
        return url

    # Don't mess with about: urls.
    if url.startswith('about:'):
        return url

    parsed = urlparse.urlparse(url)

    if parsed.scheme not in ('http', 'https', 'chrome'):
        return u''

    # Rebuild url to drop querystrings, hashes, etc
    new_url = (parsed.scheme, parsed.hostname, parsed.path, None, None, None)

    return urlparse.urlunparse(new_url)
