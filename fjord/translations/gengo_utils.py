from functools import wraps

from django.conf import settings

import json
import requests
from gengo import Gengo


class GengoError(Exception):
    """Superclass for all Gengo translation errors"""
    pass


class GengoConfigurationError(GengoError):
    """Raised when the Gengo-centric keys aren't set in settings"""
    pass


class GengoUnknownLanguage(GengoError):
    """Raised when the guesser can't guess the language"""
    pass


class GengoMachineTranslationFailure(GengoError):
    """Raised when machine translation didn't work"""
    pass


def requires_keys(fun):
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
        context for Fjord. Also, it'll make it easier to mock out the
        Gengo instance for testing.

        """
        if settings.GENGO_PUBLIC_KEY and settings.GENGO_PRIVATE_KEY:
            gengo_api = Gengo(
                public_key=settings.GENGO_PUBLIC_KEY,
                private_key=settings.GENGO_PRIVATE_KEY
            )
        else:
            gengo_api = None

        self.gengo_api = gengo_api

    @requires_keys
    def get_balance(self):
        """Returns the account balance as a float"""
        balance = self.gengo_api.getAccountBalance()
        return float(balance['response']['credits'])

    def get_language(self, text):
        """Guesses the language of the text

        :arg text: The text to guess the language of

        :raises GengoUnknownLanguage: If the request wasn't successful
            or the guesser can't figure out which language the text is

        """
        # get_language is a "private API" thing Gengo has, so it's not
        # included in the gengo library and we have to do it manually.
        resp = requests.post(
            'http://api2.gengo.com/api/service/detect/language',
            data=json.dumps({'text': text.encode('utf-8')}),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })

        resp_json = resp.json()

        if resp_json['opstat'] == 'ok':
            lang = resp_json['detected_lang_code']
            if lang == 'un':
                raise GengoUnknownLanguage('unknown language')
            return lang

        raise GengoUnknownLanguage('request failure: {0}'.format(resp.content))

    @requires_keys
    def get_machine_translation(self, id_, text):
        """Performs a machine translation through Gengo

        :arg id_: instance id
        :arg text: the text to translate

        :raises GengoUnknownLanguage: if the guesser fails to identify the
            source language of the text

        :raises GengoMachineTranslationFailure: if calling machine translation
            fails

        """
        # Note: This will throw GengoUnknownLanguage if it fails to
        # guess the language.
        lc_src = self.get_language(text)

        data = {
            'jobs': {
                'job_1': {
                    'custom_data': str(id_),
                    'body_src': text,
                    'lc_src': lc_src,
                    'lc_tgt': 'en',
                    'tier': 'machine',
                    'type': 'text',
                    'slug': 'Input machine translation',
                }
            }
        }

        resp = self.gengo_api.postTranslationJobs(
            jobs=data, as_group=0, allow_fork=0)

        if resp['opstat'] == 'ok':
            job = resp['response']['jobs']['job_1']
            if 'body_tgt' not in job:
                raise GengoMachineTranslationFailure('no body_tgt')

            return job['body_tgt']

        raise GengoMachineTranslationFailure(
            'opstat: {0}'.format(resp['opstat']))
