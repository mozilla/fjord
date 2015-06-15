import sys

import requests

from django.conf import settings

from fjord.celery import app


GOOGLE_API_URL = 'https://ssl.google-analytics.com/collect'


@app.task
def post_event(params):
    requests.post(GOOGLE_API_URL, data=params)


def ga_track_event(params, async=True):
    """Sends event tracking information to Google.

    :arg params: Params specific to the event being tracked. Particularly
        keys ``cid``, ``ec``, ``ea``, ``el`` and ``ev``.
    :arg async: Whether to do it now or later via celery.

    >>> ga_track_event({'cid': 'xxxx', 'ec': 'sumo_suggest', 'ea': 'suggest'})

    .. Note::

       If this runs in DEBUG mode or as part of a test suite, it'll
       prepend ``test_`` to the ``ec`` parameter. This reduces
       testing/development data hosing your production data.

    """
    params.update({
        'v': '1',
        # FIXME: turn this into a setting. the complexity is that it's
        # also in fjord/base/static/js/ga.js.
        'tid': 'UA-35433268-26',
        't': 'event'
    })

    # If we're in DEBUG mode or running tests, we don't want to hose
    # production data, so we prepend test_ to the category.
    if 'ec' in params and (settings.DEBUG or 'test' in sys.argv):
        params['ec'] = 'test_' + params['ec']

    if async:
        post_event.delay(params)
    else:
        post_event(params)
