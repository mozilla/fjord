import datetime
import random
import time

from django.conf import settings
from eadred.helpers import sentence_generator

from fjord.feedback.models import Response
from fjord.feedback.tests import ResponseFactory


HAPPY_FEEDBACK = (
    u'This is the best!',
    u'Firefox is great!',
    u'Firefox made me pancakes!',
    u'I love Firefox!',
    u'Firefox now my default browser!',
    u'My bestest friend!',
    u'Can\'t live without addon that vacuums my kitchen!',
    u'omg firefox awesome!',
    u'fast and secure',
    u'speedy in nature',
    u'emphasis on privacy is good',
    u'never got a virus from firefox',
    u'firefox looks awesome embedded in emacs',
    u'about:about is the best firefox page ever!',
    u'i reset my firefox profile and now it is super again!',
    u'about:mozilla! lol!',
)

SAD_FEEDBACK = (
    u'Too much orange!',
    u'Ate my baby-sister!',
    u'Firefox is too fast!',
    u'Firefox is too easy to use!',
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

PRODUCTS = (
    (u'Firefox', u'29.0'),
    (u'Firefox', u'28.0'),
    (u'Firefox', u'27.0'),
    (u'Firefox for Android', u'29.0'),
    (u'Firefox for Android', u'28.0'),
    (u'Firefox for Android', u'27.0'),
    (u'Firefox OS', u'1.2'),
    (u'Firefox OS', u'1.1'),
    (u'Firefox OS', u'1.0'),
)

PLATFORMS = (
    u'Linux',
    u'Windows 8',
    u'Mac OSX',
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

    # Firefox OS
    'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0',
)


def create_basic_sampledata():
    happy_feedback = sentence_generator(HAPPY_FEEDBACK)
    sad_feedback = sentence_generator(SAD_FEEDBACK)

    products = sentence_generator(PRODUCTS)
    platforms = sentence_generator(PLATFORMS)
    locales = sentence_generator(settings.DEV_LANGUAGES)
    urls = sentence_generator(URLS)

    # Create 100 happy responses.
    now = time.time()
    objs = []
    for i in range(100):
        product = products.next()
        now = now - random.randint(500, 2000)
        objs.append(
            ResponseFactory.build(
                happy=True,
                description=happy_feedback.next(),
                product=product[0],
                version=product[1],
                platform=platforms.next(),
                locale=locales.next(),
                created=datetime.datetime.fromtimestamp(now)
            )
        )

    # Create 100 sad responses.
    now = time.time()
    for i in range(100):
        product = products.next()
        now = now - random.randint(500, 2000)
        objs.append(
            ResponseFactory.build(
                happy=False,
                description=sad_feedback.next(),
                product=product[0],
                version=product[1],
                platform=platforms.next(),
                locale=locales.next(),
                url=urls.next(),
                created=datetime.datetime.fromtimestamp(now)
            )
        )

    Response.objects.bulk_create(objs)


def create_additional_sampledata(samplesize):
    samplesize = int(samplesize)

    print 'Working on generating {0} feedback responses....'.format(
        samplesize)

    happy_feedback = sentence_generator(HAPPY_FEEDBACK)
    sad_feedback = sentence_generator(SAD_FEEDBACK)
    products = sentence_generator(PRODUCTS)
    urls = sentence_generator(URLS)
    user_agents = sentence_generator(USER_AGENTS)
    locales = sentence_generator(settings.DEV_LANGUAGES)

    objs = []

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

        product = products.next()
        objs.append(
            ResponseFactory.build(
                happy=happy,
                description=description,
                product=product[0],
                version=product[1],
                url=url,
                user_agent=user_agents.next(),
                locale=locales.next(),
                created=datetime.datetime.fromtimestamp(now)
            )
        )

        # Bulk-save the objects to the db 500 at a time and
        # print something to stdout about it.
        if i % 500 == 0:
            Response.objects.bulk_create(objs)
            objs = []
            print '  {0}...'.format(i)

    if objs:
        print '  {0}...'.format(samplesize)
        Response.objects.bulk_create(objs)
        objs = []


def generate_sampledata(options):
    """Generates response data.

    Usage: ``./manage.py generatedata [--with=samplesize=n]``

    If you specify a samplesize, then it randomly generates that
    many responses.

    Otherwise it generates 5 happy and 5 sad responses.

    """
    samplesize = options.get('samplesize')

    if samplesize not in (None, True):
        create_additional_sampledata(samplesize)
    else:
        create_basic_sampledata()

    print 'Done!  Please reindex to pick up db changes.'
