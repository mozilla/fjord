import random
from functools import wraps
from string import letters

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import LiveServerTestCase
from django.test import TestCase as OriginalTestCase
from django.test.client import Client
from django.test.utils import override_settings

from django_browserid.tests import mock_browserid
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox import firefox_binary
from nose import SkipTest

# reverse is here for convenience so other test modules import it from
# here rather than importing it from funfactory
from funfactory.urlresolvers import split_path, reverse

from fjord.base.models import Profile


class LocalizingClient(Client):
    """Client which rewrites urls to include locales and adds a user agent.

    This prevents the locale middleware from returning a 301 to add the
    prefixes, which makes tests more complicated.

    It also ensures there is a user agent set in the header. The default is a
    Firefox 14 on Linux user agent. It can be overridden by passing a
    user_agent parameter to ``__init__``, setting ``self.user_agent`` to the
    desired value, or by including ``HTTP_USER_AGENT`` in an individual
    request. This behavior can be prevented by setting ``self.user_agent`` to
    ``None``.

    """
    def __init__(self, user_agent=None, *args, **kwargs):
        self.user_agent = user_agent or ('Mozilla/5.0 (X11; Linux x86_64; '
            'rv:14.0) Gecko/20100101 Firefox/14.0.1')
        super(LocalizingClient, self).__init__(*args, **kwargs)

    def request(self, **request):
        """Make a request, ensuring it has a locale and a user agent."""
        # Fall back to defaults as in the superclass's implementation:
        path = request.get('PATH_INFO', self.defaults.get('PATH_INFO', '/'))
        locale, shortened = split_path(path)
        if not locale:
            request['PATH_INFO'] = '/%s/%s' % (settings.LANGUAGE_CODE,
                                               shortened)
        if 'HTTP_USER_AGENT' not in request and self.user_agent:
            request['HTTP_USER_AGENT'] = self.user_agent

        return super(LocalizingClient, self).request(**request)


class BaseTestCase(OriginalTestCase):
    def client_login_user(self, user):
        with mock_browserid(user.email):
            ret = self.client.login(audience='faux', assertion='faux')
            assert ret, "Login failed."

    def setUp(self):
        super(BaseTestCase, self).setUp()
        cache.clear()

    def tearDown(self):
        super(BaseTestCase, self).tearDown()
        cache.clear()


@override_settings(ES_LIVE_INDEX=False)
class TestCase(BaseTestCase):
    """TestCase that skips live indexing."""
    pass


class MobileTestCase(TestCase):
    """Base class for mobile tests"""
    def setUp(self):
        super(MobileTestCase, self).setUp()
        self.client.cookies[settings.MOBILE_COOKIE] = 'on'


# FIXME: This doesn't work right in regards to transactions and data
# in the db that's put there via data migrations.
#
# It's essentially this problem here:
#
# https://groups.google.com/forum/#!msg/south-users/U7tz5RmhJaU/8Ec-3N77O7QJ
#
# Need to fix that before we can re-enable this.
#
# Commenting this and the two Seleniunm test cases out for now because
# I really want this to be a huge eyesore so it's likely to get fixed.
# class SeleniumTestCase(LiveServerTestCase):
#     skipme = False

#     @classmethod
#     def setUpClass(cls):
#         try:
#             firefox_path = getattr(settings, 'SELENIUM_FIREFOX_PATH', None)
#             if firefox_path:
#                 firefox_bin = firefox_binary.FirefoxBinary(
#                     firefox_path=firefox_path)
#                 kwargs = {'firefox_binary': firefox_bin}
#             else:
#                 kwargs = {}
#             cls.webdriver = webdriver.Firefox(**kwargs)
#         except (RuntimeError, WebDriverException):
#             cls.skipme = True
#         super(SeleniumTestCase, cls).setUpClass()

#     @classmethod
#     def tearDownClass(cls):
#         super(SeleniumTestCase, cls).tearDownClass()
#         if not cls.skipme:
#             cls.webdriver.quit()

#     def setUp(self):
#         super(SeleniumTestCase, self).setUp()
#         # Don't run if Selenium isn't available.
#         if self.skipme:
#             raise SkipTest('Selenium unavailable.')
#         # Go to an empty page before every test.
#         self.webdriver.get('')
#         cache.clear()

#     def tearDown(self):
#         super(SeleniumTestCase, self).tearDown()
#         cache.clear()


def with_save(func):
    """Decorate a model maker to add a `save` kwarg.

    If save=True, the model maker will save the object before returning it.

    """
    @wraps(func)
    def saving_func(*args, **kwargs):
        save = kwargs.pop('save', False)
        ret = func(*args, **kwargs)
        if save:
            ret.save()
        return ret

    return saving_func


@with_save
def user(**kwargs):
    """Return a user with all necessary defaults filled in.

    Default password is 'testpass' unless you say otherwise in a kwarg.

    """
    defaults = {}
    if 'username' not in kwargs:
        defaults['username'] = ''.join(random.choice(letters)
                                       for x in xrange(15))
    if 'email' not in kwargs:
        defaults['email'] = ''.join(
            random.choice(letters) for x in xrange(10)) + '@example.com'
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_password(kwargs.get('password', 'testpass'))
    return user


@with_save
def profile(**kwargs):
    """Returns a Profile"""
    defaults = {}
    if 'user' not in kwargs:
        defaults['user'] = user(save=True)

    defaults.update(kwargs)

    return Profile(**defaults)
