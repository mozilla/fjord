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
    u'https://fjord.readthedocs.io/en/latest/',
    u'http://mozilla.org/',
)

ALWAYS_API = ['Firefox OS']

NEVER_API = ['Firefox']

PRODUCT_TUPLES = (
    # product, version, platform, user_agent, api?
    (u'Firefox', u'17.0', u'Linux', u'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0'),  # noqa
    (u'Firefox', u'22.0', u'Linux', u'Mozilla/5.0 (X11; Linux i686; rv:22.0) Gecko/20130306 Firefox/22.0'),  # noqa

    (u'Firefox', u'18.0', u'Mac OSX', u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'),  # noqa
    (u'Firefox', u'20.0', u'Mac OSX', u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:20.0) Gecko/20130208 Firefox/20.0'),  # noqa

    (u'Firefox', u'10.0', u'Windows', u'Mozilla/5.0 (Windows NT 5.1; rv:10.0) Gecko/20100101 Firefox/10.0'),  # noqa
    (u'Firefox', u'13.0.1', u'Windows', u'Mozilla/5.0 (Windows NT 5.1; rv:13.0) Gecko/20100101 Firefox/13.0.1'),  # noqa
    (u'Firefox', u'19.0', u'Windows', u'Mozilla/5.0 (Windows NT 5.1; rv:19.0) Gecko/20100101 Firefox/19.0'),  # noqa

    (u'Firefox for Android', u'14.0.2', u'Android', u'Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0.2'),  # noqa

    (u'Firefox OS', u'1.0', u'Firefox OS', u'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0'),  # noqa
    (u'Firefox OS', u'1.1', u'Firefox OS', u'Mozilla/5.0 (Mobile; rv:18.1) Gecko/18.1 Firefox/18.1'),  # noqa
)


def locale_generator():
    while True:
        if random.choice((True, False)):
            yield 'en-US'
        elif random.choice((True, False)):
            yield random.choice(('es', 'de', 'fr', 'pt-BR'))
        else:
            yield random.choice(settings.PROD_LANGUAGES)


def create_basic_sampledata():
    print 'Generating 100 happy and 100 sad responses...'
    happy_feedback = sentence_generator(HAPPY_FEEDBACK)
    sad_feedback = sentence_generator(SAD_FEEDBACK)

    # Note: We're abusing sentence_generator to just return random
    # choice from a tuple of things.
    products = sentence_generator(PRODUCT_TUPLES)
    locales = locale_generator()
    urls = sentence_generator(URLS)

    # Create 100 happy responses.
    now = time.time()
    objs = []
    for i in range(100):
        product = products.next()
        now = now - random.randint(500, 2000)
        if product[0] in ALWAYS_API:
            api = '1'
        elif product[0] in NEVER_API:
            api = None
        else:
            api = random.choice(('1', None))

        objs.append(
            ResponseFactory.build(
                happy=True,
                description=happy_feedback.next(),
                product=product[0],
                version=product[1],
                platform=product[2],
                user_agent=product[3],
                locale=locales.next(),
                created=datetime.datetime.fromtimestamp(now),
                api=api
            )
        )

    # Create 100 sad responses.
    now = time.time()
    for i in range(100):
        product = products.next()
        now = now - random.randint(500, 2000)
        if product[0] in ALWAYS_API:
            api = '1'
        elif product[0] in NEVER_API:
            api = None
        else:
            api = random.choice(('1', None))
        objs.append(
            ResponseFactory.build(
                happy=False,
                description=sad_feedback.next(),
                product=product[0],
                version=product[1],
                platform=product[2],
                locale=locales.next(),
                user_agent=product[3],
                url=urls.next(),
                created=datetime.datetime.fromtimestamp(now),
                api=api
            )
        )

    Response.objects.bulk_create(objs)


def create_additional_sampledata(samplesize='1000'):
    samplesize = int(samplesize)

    print 'Generating {0} feedback responses...'.format(samplesize)

    happy_feedback = sentence_generator(HAPPY_FEEDBACK)
    sad_feedback = sentence_generator(SAD_FEEDBACK)
    products = sentence_generator(PRODUCT_TUPLES)
    urls = sentence_generator(URLS)
    locales = locale_generator()

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
        if product[0] in ALWAYS_API:
            api = '1'
        elif product[0] in NEVER_API:
            api = None
        else:
            api = random.choice(('1', None))
        objs.append(
            ResponseFactory.build(
                happy=happy,
                description=description,
                product=product[0],
                version=product[1],
                platform=product[2],
                url=url,
                user_agent=product[3],
                locale=locales.next(),
                created=datetime.datetime.fromtimestamp(now),
                api=api
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

    Generates 50 happy and 50 sad and 1000 additional responses.

    """
    samplesize = options.get('samplesize', '1000')

    create_basic_sampledata()
    create_additional_sampledata(samplesize)

    print 'Done! Please run "./manage.py esreindex" to pick up db changes.'
