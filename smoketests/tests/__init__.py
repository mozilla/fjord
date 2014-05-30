"""The base infrastructure for smoketests.

This is based in large part on the mozwebqa code, but it's slimmed
down for the bits we need. This makes it easier to copy code back and
forth between these smoketests and the input-tests repository.

* https://github.com/davehunt/pytest-mozwebqa
* https://github.com/mozilla/input-tests

"""

import os

from functools import wraps
from unittest import TestCase

from nose import SkipTest
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

YES_PLEASE = ('1', 'y', 'yes', 't', 'true')


class Config(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    
def get_setup():
    defaults = {
        'base_url': 'http://localhost:8000',
        'destructive': '0',
        'driver': 'firefox',
        'firefox_path': None,
        'profile_path': None,
        'timeout': 60,
    }

    for key, val in defaults.items():
        newval = os.environ.get(key.upper(), val)
        if isinstance(val, int):
            newval = int(newval)
        defaults[key] = newval

    return Config(**defaults)


class Client(object):
    def __init__(self, options):
        self.base_url = options.base_url

        self.driver = options.driver
        self.firefox_path = options.firefox_path
        self.profile_path = options.profile_path
        self.timeout = options.timeout

        self.default_implicit_wait = 10

    def start(self):
        self.start_webdriver_client()
        self.selenium.implicitly_wait(self.default_implicit_wait)

    def start_webdriver_client(self):
        firefox_path = self.firefox_path
        binary = firefox_path and FirefoxBinary(firefox_path) or None

        profile_path = self.profile_path
        profile = webdriver.FirefoxProfile(profile_path)

        self.selenium =webdriver.Firefox(
            firefox_binary=binary,
            firefox_profile=profile
        )

    @property
    def session_id(self):
        return self.selenium.session_id

    @property
    def url(self):
        try:
            return self.selenium.current_url
        except Exception:
            return None

    def stop(self):
        try:
            self.selenium.quit()
        except Exception:
            pass


def nondestructive(fun):
    """Function/method decorator for marking non-destructive tests

    Use this decorator to mark tests that are non-destructive. Any
    tests not marked as such are assumed to be destructive and will
    be skipped unless explicitly enabled.

    """
    @wraps(fun)
    def _nondestructive(*args, **kwargs):
        return fun(*args, **kwargs)

    _nondestructive._not_destructive = True
    return _nondestructive


def add_mozwebqa(fun):
    @wraps(fun)
    def _add_mozwebqa(self, *args, **kwargs):
        return fun(self, self.get_mozwebqa(), *args, **kwargs)

    # Pass _not_destructive flag
    setattr(_add_mozwebqa, '_not_destructive',
            getattr(fun, '_not_destructive', False))
    return _add_mozwebqa


class DestructiveCheckerMetaClass(type):
    def __new__(cls, name, base, attrs):
        config = get_setup()

        for fn, fun in attrs.items():
            if not fn.startswith('test') or not callable(fun):
                continue

            attrs[fn] = add_mozwebqa(fun)
            nd = getattr(fun, '_not_destructive', False)

            if nd:
                continue

            if config.destructive in YES_PLEASE:
                # Run destructive tests only if explicitly told to do so
                continue

            @wraps(fun)
            def skip_me_i_am_dangerous(*args, **kwargs):
                msg = 'Destructive test. RUN FOR YOUR LIVES! ({0})'.format(fn)
                raise SkipTest(msg)
            attrs[fn] = skip_me_i_am_dangerous

        return super(DestructiveCheckerMetaClass, cls).__new__(
            cls, name, base, attrs)


class BaseTestCase(TestCase):
    """Base test case class for all smoketests"""
    __metaclass__ = DestructiveCheckerMetaClass

    def get_mozwebqa(self):
        """This mimics mozwebqa stuff."""
        class TestSetup(object):
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        return TestSetup(
            base_url=self.base_url,
            selenium=self.selenium,
            timeout=self.timeout
        )

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.options = get_setup()

        self.selenium_client = Client(get_setup())
        self.selenium_client.start()
        self.session_id = self.selenium_client.session_id
        self.selenium = self.selenium_client.selenium
        self.timeout = self.selenium_client.timeout
        self.base_url = self.options.base_url

    def tearDown(self):
        super(BaseTestCase, self).tearDown()
        self.selenium_client.stop()
