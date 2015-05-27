import json
import logging

import requests
from tower import ugettext as _

from fjord.base.google_utils import ga_track_event
from fjord.suggest import Link, Suggester
from fjord.redirector import Redirector, build_redirect_url


PROVIDER = 'sumosuggest'
# Increment this any time we change the heuristics for creating
# suggestions.
PROVIDER_VERSION = 1

EVENT_CATEGORY = 'sumo_suggest'

SUMO_HOST = 'https://support.mozilla.org'
SUMO_SUGGEST_API_URL = SUMO_HOST + '/api/2/search/suggest/'
SUMO_SUGGEST_SESSION_KEY = 'sumo_suggest_docs_{0}'
SUMO_AAQ_URL = 'https://support.mozilla.org/questions/new'


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
    docs = resp.json()['documents']
    return [
        {
            'summary': doc['title'],
            'description': doc['summary'],
            'url': SUMO_HOST + doc['url']
        }
        for doc in docs
    ]


class RedirectParseError(Exception):
    pass


def format_redirect(rank):
    return 'sumosuggest.{0}'.format(rank)


def parse_redirect(redirect):
    try:
        trigger, rank = redirect.split('.')
        if rank != 'aaq':
            rank = int(rank)
        return trigger, rank
    except (ValueError, IndexError, TypeError) as exc:
        raise RedirectParseError(str(exc))


class SUMOSuggestRedirector(Redirector):
    """Provides redirection urls

    """
    def handle_redirect(self, request, redirect):
        # If it's not a sumosuggest redirect, return.
        if not redirect.startswith('sumosuggest'):
            return

        # Get the response id for the last feedback left.
        response_id = request.session.get('response_id', None)
        if response_id is None:
            return

        # If the session has no links, then we have nothing to
        # redirect to, so return.
        session_key = SUMO_SUGGEST_SESSION_KEY.format(response_id)
        docs = request.session.get(session_key, None)
        if not docs:
            return

        # Extract the rank.
        try:
            trigger, rank = parse_redirect(redirect)
        except RedirectParseError:
            return

        if rank == 'aaq':
            url = SUMO_AAQ_URL
        else:
            try:
                url = docs[rank]['url']
            except IndexError:
                # This doc doesn't exist.
                return

        ga_track_event({
            'cid': str(response_id),
            'ec': EVENT_CATEGORY,
            'ea': 'view' if rank != 'aaq' else 'viewaaq',
            'el': url
        })

        return url


class SUMOSuggest(Suggester):
    """Provides suggest links based on SUMO Search Suggest API results

    .. Note::

       If you add this provider, you should also add the related
       redirector. If you don't, you'll get busted links.

    """
    def docs_to_links(self, docs):
        """Converts docs from SUMO Suggest API to links and adds AAQ link"""
        links = [
            Link(
                provider=PROVIDER,
                provider_version=PROVIDER_VERSION,
                summary=doc['summary'],
                description=doc['description'],
                url=build_redirect_url(format_redirect(i))
            )
            for i, doc in enumerate(docs)
        ]
        links.append(
            Link(
                provider=PROVIDER,
                provider_version=PROVIDER_VERSION,
                summary=_(u'Having problems? Get help.'),
                description=_(
                    'Go to our support forum where you can get help and '
                    'find answers.'
                ),
                url=build_redirect_url(format_redirect('aaq'))
            )
        )
        return links

    def get_suggestions(self, feedback, request=None):
        # Note: We only want to run suggestions for sad responses for
        # Firefox product with en-US locale and for feedback that has
        # more than 7 words.
        #
        # If any of that changes, we'll need to rethink this.
        if ((feedback.happy
             or feedback.locale != u'en-US'
             or feedback.product != u'Firefox'
             or len(feedback.description.split()) < 7)):
            return []

        session_key = SUMO_SUGGEST_SESSION_KEY.format(feedback.id)

        # Check the session to see if we've provided links already and
        # if so, re-use those.
        if request is not None:
            docs = request.session.get(session_key, None)
            if docs is not None:
                return self.docs_to_links(docs)

        try:
            docs = get_kb_articles(u'en-US', u'Firefox', feedback.description)
        except Exception:
            # FIXME: As we discover what exceptions actually get
            # kicked up, we can handle them individually as
            # appropriate.
            logger.exception('SUMO Suggest API raised exception.')
            return []

        ga_track_event({
            'cid': str(feedback.id),
            'ec': EVENT_CATEGORY,
            'ea': 'suggest'
        })

        links = self.docs_to_links(docs)

        if request is not None:
            request.session[session_key] = docs

        return links
