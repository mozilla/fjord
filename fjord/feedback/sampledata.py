import datetime
import random
import time

from django.conf import settings
from eadred.helpers import sentence_generator

from fjord.feedback.tests import response


HAPPY_FEEDBACK = (
    u'This is the best!',
    u'Firefox is great!',
    u'Made me pancakes!',
    u'I love it!',
    u'Firefox now my default browser!',
    u'My bestest friend!',
    u'Can\'t live without addon that vacuums my kitchen!',
    u'fast and secure',
    u'speedy in nature',
    u'emphasis on privacy is good',
    u'never got a virus from firefox',
    u'looks awesome embedded in emacs',
    u'about:about is the best!',
    u'i reset my profile and now it is super again!',
    u'about:mozilla! lol!',
)

SAD_FEEDBACK = (
    u'Too much orange!',
    u'Ate my baby-sister!',
    u'Too fast!',
    u'Too easy to use!',
    u'garbage collection keeps downstairs neighbors awake.',
    u'Parked my car in wrong spot!',
    u'reminds me of succulant milk chocolate and i can\'t eat dairy.',
    u'No commercial at superbowl.',
)

URLS = (
    u'http://google.com/',
    u'http://example.com/',
    u'http://pyvideo.org/',
    u'http://github.com/mozilla/fjord',
    u'https://fjord.readthedocs.org/en/latest/',
    u'http://mozilla.org/',
)

USER_AGENTS = (
    # Linux
    'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0',
    'Mozilla/5.0 (X11; Linux i686; rv:22.0) Gecko/20130306 Firefox/22.0',

    # OS X
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 '
    'Firefox/18.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:20.0) Gecko/20130208 '
    'Firefox/20.0',

    # Windows
    'Mozilla/5.0 (Windows NT 5.1; rv:10.0) Gecko/20100101 Firefox/10.0',
    'Mozilla/5.0 (Windows NT 5.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
    'Mozilla/5.0 (Windows NT 5.1; rv:19.0) Gecko/20100101 Firefox/19.0',

    # Android
    'Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0.2',
)


def generate_sampledata(options):
    """Generates response data.

    Usage: ``./manage.py generatedata [--with=samplesize=n]``

    If you specify a samplesize, then it randomly generates that
    many responses.

    Otherwise it generates 5 happy and 5 sad responses.

    """
    samplesize = options.get('samplesize')

    if samplesize not in (None, True):
        samplesize = int(samplesize)

        happy_feedback = sentence_generator(HAPPY_FEEDBACK)
        sad_feedback = sentence_generator(SAD_FEEDBACK)
        urls = sentence_generator(URLS)
        user_agents = sentence_generator(USER_AGENTS)
        locales = sentence_generator(settings.DEV_LANGUAGES)

        now = time.time()
        for i in range(samplesize):
            now = now - random.randint(500, 2000)

            happy = random.choice([True, False])
            if happy:
                description = happy_feedback.next()
                url = u''
            else:
                description = sad_feedback.next()
                url = urls.next()

            response(
                happy=happy,
                description=description,
                url=url,
                ua=user_agents.next(),
                locale=locales.next(),
                created=datetime.datetime.fromtimestamp(now),
                save=True)
        return

    # Create 5 happy responses.
    for i in range(5):
        response(happy=True, description=HAPPY_FEEDBACK[i], save=True)

    # Create 5 sad responses.
    for i in range(5):
        response(happy=False, description=SAD_FEEDBACK[i], url=URLS[i],
                 save=True)
