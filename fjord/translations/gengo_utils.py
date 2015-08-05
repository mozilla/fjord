from functools import wraps

from django.conf import settings

import json
import requests
from gengo import Gengo, GengoError  # noqa


# Cache of supported languages from Gengo. Theoretically, these don't
# change often, so the first time we request it, we cache it and then
# keep that until the next deployment.
GENGO_LANGUAGE_CACHE = None

# Cache of supported language pairs.
GENGO_LANGUAGE_PAIRS_CACHE = None

# List of manually-curated languages that don't work for machine
# translation src
# Note: Gengo doesn't have an API that tells us these, so we have
# to add them as we hit them. :(
GENGO_UNSUPPORTED_MACHINE_LC_SRC = [
    'cs',
    'hu',
    'tr'
]

# The comment we send to Gengo with the jobs to give some context for
# the job.
GENGO_COMMENT = """\
This is a response from the Mozilla Input feedback system. It was
submitted by an anonymous user in a non-English language. The feedback
is used in aggregate to determine general user sentiment about Mozilla
products and its features.

This translation job was created by an automated system, so we're
unable to respond to translator comments.

If the response is nonsensical or junk text, then write "spam".
"""

GENGO_DETECT_LANGUAGE_API = 'https://api.gengo.com/service/detect_language'


class FjordGengoError(Exception):
    """Superclass for all Gengo translation errors"""
    pass


class GengoConfigurationError(FjordGengoError):
    """Raised when the Gengo-centric keys aren't set in settings"""


class GengoUnknownLanguage(FjordGengoError):
    """Raised when the guesser can't guess the language"""


class GengoUnsupportedLanguage(FjordGengoError):
    """Raised when the guesser guesses a language Gengo doesn't support

    .. Note::

       If you buy me a beer, I'll happily tell you how I feel about
       this.

    """


class GengoAPIFailure(FjordGengoError):
    """Raised when the api kicks up an error"""


class GengoMachineTranslationFailure(FjordGengoError):
    """Raised when machine translation didn't work"""


class GengoHumanTranslationFailure(FjordGengoError):
    """Raised when human translation didn't work"""


def requires_keys(fun):
    """Throw GengoConfigurationError if keys aren't set"""
    @wraps(fun)
    def _requires_keys(self, *args, **kwargs):
        if not self.gengo_api:
            raise GengoConfigurationError()
        return fun(self, *args, **kwargs)
    return _requires_keys


class FjordGengo(object):
    def __init__(self):
        """Constructs a FjordGengo wrapper around the Gengo class

        We do this to make using the API a little easier in the
        context for Fjord as it includes the business logic around
        specific use cases we have.

        Also, having all the Gengo API stuff in one place makes it
        easier for mocking when testing.

        """
        if settings.GENGO_PUBLIC_KEY and settings.GENGO_PRIVATE_KEY:
            gengo_api = Gengo(
                public_key=settings.GENGO_PUBLIC_KEY,
                private_key=settings.GENGO_PRIVATE_KEY,
                sandbox=getattr(settings, 'GENGO_USE_SANDBOX', True)
            )
        else:
            gengo_api = None

        self.gengo_api = gengo_api

    def is_configured(self):
        """Returns whether Gengo is configured for Gengo API requests"""
        return not (self.gengo_api is None)

    @requires_keys
    def get_balance(self):
        """Returns the account balance as a float"""
        balance = self.gengo_api.getAccountBalance()
        return float(balance['response']['credits'])

    @requires_keys
    def get_languages(self, raw=False):
        """Returns the list of supported language targets

        :arg raw: True if you want the whole response, False if you
            want just the list of languages

        .. Note::

           This is cached until the next deployment.

        """
        global GENGO_LANGUAGE_CACHE
        if not GENGO_LANGUAGE_CACHE:
            resp = self.gengo_api.getServiceLanguages()
            GENGO_LANGUAGE_CACHE = (
                resp,
                tuple([item['lc'] for item in resp['response']])
            )
        if raw:
            return GENGO_LANGUAGE_CACHE[0]
        else:
            return GENGO_LANGUAGE_CACHE[1]

    @requires_keys
    def get_language_pairs(self):
        """Returns the list of supported language pairs for human translation

        .. Note::

           This is cached until the next deployment.

        """
        global GENGO_LANGUAGE_PAIRS_CACHE
        if not GENGO_LANGUAGE_PAIRS_CACHE:
            resp = self.gengo_api.getServiceLanguagePairs()
            # NB: This looks specifically at the standard tier because
            # that's what we're using. It ignores the other tiers.
            pairs = [(item['lc_src'], item['lc_tgt'])
                     for item in resp['response']
                     if item['tier'] == u'standard']
            GENGO_LANGUAGE_PAIRS_CACHE = pairs

        return GENGO_LANGUAGE_PAIRS_CACHE

    @requires_keys
    def get_job(self, job_id):
        """Returns data for a specified job

        :arg job_id: the job_id for the job we want data for

        :returns: dict of job data

        """
        resp = self.gengo_api.getTranslationJob(id=str(job_id))

        if resp['opstat'] != 'ok':
            raise GengoAPIFailure(
                'opstat: {0}, response: {1}'.format(resp['opstat'], resp))

        return resp['response']['job']

    def guess_language(self, text):
        """Guesses the language of the text

        :arg text: text to guess the language of

        :raises GengoUnknownLanguage: if the request wasn't successful
            or the guesser can't figure out which language the text is

        """
        # get_language is a "private API" thing Gengo has, so it's not
        # included in the gengo library and we have to do it manually.
        resp = requests.post(
            GENGO_DETECT_LANGUAGE_API,
            data=json.dumps({'text': text.encode('utf-8')}),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })

        try:
            resp_json = resp.json()
        except ValueError:
            # If it's not JSON, then I don't really know what it is,
            # so I want to see it in an error email. Chances are it's
            # some ephemeral problem.
            #
            # FIXME: Figure out a better thing to do here.
            raise GengoAPIFailure(
                u'ValueError: non-json response: {0} {1}'.format(
                    resp.status_code, resp.text))

        if 'detected_lang_code' in resp_json:
            lang = resp_json['detected_lang_code']
            if lang == 'un':
                raise GengoUnknownLanguage('unknown language')
            return lang

        raise GengoUnknownLanguage('request failure: {0}'.format(resp.content))

    @requires_keys
    def translate_bulk(self, jobs):
        """Performs translation through Gengo on multiple jobs

        Translation is asynchronous--this method posts the translation
        jobs and then returns the order information for those jobs
        to be polled at a later time.

        :arg jobs: a list of dicts with ``id``, ``lc_src``, ``lc_dst``
            ``tier``, ``text`` and (optional) ``unique_id`` keys

        Response dict includes:

        * job_count: number of jobs processed
        * order_id: the order id
        * group_id: I have no idea what this is
        * credits_used: the number of credits used
        * currency: the currency the credits are in

        """
        payload = {}
        for job in jobs:
            payload['job_{0}'.format(job['id'])] = {
                'body_src': job['text'],
                'lc_src': job['lc_src'],
                'lc_tgt': job['lc_dst'],
                'tier': job['tier'],
                'type': 'text',
                'slug': 'Mozilla Input feedback response',
                'force': 1,
                'comment': GENGO_COMMENT,
                'purpose': 'Online content',
                'tone': 'informal',
                'use_preferred': 0,
                'auto_approve': 1,
                'custom_data': job.get('unique_id', job['id'])
            }

        resp = self.gengo_api.postTranslationJobs(jobs=payload)
        if resp['opstat'] != 'ok':
            raise GengoAPIFailure(
                'opstat: {0}, response: {1}'.format(resp['opstat'], resp))

        return resp['response']

    @requires_keys
    def completed_jobs_for_order(self, order_id):
        """Returns jobs for an order which are completed

        Gengo uses the status "approved" for jobs that have been
        translated and approved and are completed.

        :arg order_id: the order_id for the jobs we want to look at

        :returns: list of job data dicts; interesting fields being
            ``custom_data`` and ``body_tgt``

        """
        resp = self.gengo_api.getTranslationOrderJobs(id=str(order_id))

        if resp['opstat'] != 'ok':
            raise GengoAPIFailure(
                'opstat: {0}, response: {1}'.format(resp['opstat'], resp))

        job_ids = resp['response']['order']['jobs_approved']
        if not job_ids:
            return []

        job_ids = ','.join(job_ids)
        resp = self.gengo_api.getTranslationJobBatch(id=job_ids)

        if resp['opstat'] != 'ok':
            raise GengoAPIFailure(
                'opstat: {0}, response: {1}'.format(resp['opstat'], resp))

        return resp['response']['jobs']
