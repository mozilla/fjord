import json
import logging

import requests

from fjord.suggest import Link, Provider


PROVIDER = 'sumosuggest'
# Increment this any time we change the heuristics for creating
# suggestions.
PROVIDER_VERSION = 1

SUMO_SUGGEST_API_URL = 'https://support.mozilla.org/api/2/search/suggest/'


logger = logging.getLogger('i.sumosuggest')


def get_kb_articles(locale, product, text):
    """Retrieves kb articles using the SUMO search suggest API

    Throws a variety of exceptions all of which the caller should
    deal with.

    :arg text: The text to search
    """
    params = {
        'q': text,
        'locale': 'en-US',
        'product': 'firefox',
        'max_documents': 3,
        'max_questions': 0
    }
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
    }
    resp = requests.get(
        SUMO_SUGGEST_API_URL,
        data=json.dumps(params),
        headers=headers,
        # This is slightly larger than 3 which is what the requests
        # docs suggest, but we really want the shortest timeout we can
        # get away with since this happens during the http request
        # handling cycle.
        timeout=3.5
    )
    return resp.json()['documents']


class SUMOSuggestProvider(Provider):
    def get_suggestions(self, response):
        # Note: We only want to run suggestions for sad responses for
        # Firefox product with en-US locale and for feedback that has
        # more than 7 words.
        #
        # If any of that changes, we'll need to rethink this.
        if ((response.happy
             or response.locale != u'en-US'
             or response.product != u'Firefox'
             or len(response.description.split()) < 7)):
            return []

        try:
            docs = get_kb_articles(u'en-US', u'Firefox', response.description)
        except Exception:
            # FIXME: As we discover what exceptions actually get
            # kicked up, we can handle them individually as
            # appropriate.
            logger.exception('SUMO Suggest API raised exception.')
            return []

        return [
            Link(
                provider=PROVIDER,
                provider_version=PROVIDER_VERSION,
                summary=doc['title'],
                description=doc['summary'],
                url=doc['url']
            )
            for doc in docs
        ]
