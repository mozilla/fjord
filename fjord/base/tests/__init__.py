from functools import wraps

from django.conf import settings
from django.test.client import Client

from funfactory.urlresolvers import split_path, reverse
from test_utils import TestCase


class LocalizingClient(Client):
    """Client which prepends a locale so test requests can get through
    LocaleURLMiddleware without resulting in a locale-prefix-adding 301.

    Otherwise, we'd have to hard-code locales into our tests everywhere or
    {mock out reverse() and make LocaleURLMiddleware not fire}.

    """
    def request(self, **request):
        """Make a request, but prepend a locale if there isn't one already."""
        # Fall back to defaults as in the superclass's implementation:
        path = request.get('PATH_INFO', self.defaults.get('PATH_INFO', '/'))
        locale, shortened = split_path(path)
        if not locale:
            request['PATH_INFO'] = '/%s/%s' % (settings.LANGUAGE_CODE,
                                               shortened)
        return super(LocalizingClient, self).request(**request)


class MobileTestCase(TestCase):
    """Base class for mobile tests"""
    def setUp(self):
        super(MobileTestCase, self).setUp()
        self.client.cookies[settings.MOBILE_COOKIE] = 'on'


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
