#!/usr/bin/env python
import logging
import os
import site
import sys


current_settings = None
execute_manager = None
log = logging.getLogger(__name__)
ROOT = None


def path(*a):
    if ROOT is None:
        _not_setup()
    return os.path.join(ROOT, *a)


def setup_environ(manage_file):
    """Sets up a Django app within a manage.py file"""
    # sys is global to avoid undefined local
    global sys, current_settings, execute_manager, ROOT

    ROOT = os.path.dirname(os.path.abspath(manage_file))

    # Adjust the python path and put local packages in front.
    prev_sys_path = list(sys.path)

    # Make root application importable without the need for
    # python setup.py install|develop
    sys.path.append(ROOT)

    # Global (upstream) vendor library
    site.addsitedir(path('vendor'))

    # Move the new items to the front of sys.path. (via virtualenv)
    new_sys_path = []
    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path

    from django.core.management import execute_manager  # noqa

    from fjord.settings import local as settings
    current_settings = settings
    validate_settings(settings)


def validate_settings(settings):
    """
    Raise an error in prod if we see any insecure settings.

    This used to warn during development but that was changed in
    71718bec324c2561da6cc3990c927ee87362f0f7
    """
    from django.core.exceptions import ImproperlyConfigured
    if settings.SECRET_KEY == '':
        msg = 'settings.SECRET_KEY cannot be blank! Check your local settings'
        if not settings.DEBUG:
            raise ImproperlyConfigured(msg)

    if getattr(settings, 'SESSION_COOKIE_SECURE', None) is None:
        msg = ('settings.SESSION_COOKIE_SECURE should be set to True; '
               'otherwise, your session ids can be intercepted over HTTP!')
        if not settings.DEBUG:
            raise ImproperlyConfigured(msg)

    hmac = getattr(settings, 'HMAC_KEYS', {})
    if not len(hmac.keys()):
        msg = 'settings.HMAC_KEYS cannot be empty! Check your local settings'
        if not settings.DEBUG:
            raise ImproperlyConfigured(msg)


def import_mod_by_name(target):
    # stolen from mock :)
    components = target.split('.')
    import_path = components.pop(0)
    thing = __import__(import_path)

    for comp in components:
        import_path += ".%s" % comp
        thing = _dot_lookup(thing, comp, import_path)
    return thing


def _dot_lookup(thing, comp, import_path):
    try:
        return getattr(thing, comp)
    except AttributeError:
        __import__(import_path)
        return getattr(thing, comp)


def _not_setup():
    raise EnvironmentError(
            'setup_environ() has not been called for this process')


def main():
    if current_settings is None:
        _not_setup()
    execute_manager(current_settings)
