#!/usr/bin/env python
import logging
import os
import site
import sys
from itertools import chain


current_settings = None
execute_from_command_line = None
log = logging.getLogger(__name__)
ROOT = None


def path(*a):
    if ROOT is None:
        _not_setup()
    return os.path.join(ROOT, *a)


def check_dependencies():
    """Check installed requirements vs. specified requirements

    This prints out a list of dependencies where the version installed
    is not the same as the one specified in the requirements files.

    It also exits immediately. At some point we might want to change
    it from doing that, but not today.

    If you want to skip this check, set SKIP_CHECK=1 in your
    environment.

    .. Note::

       This only works for packaged requirements. It does not work for
       requirements downloaded in a tarball from github. Those
       requirements get put in the "unsatisfyable" requirements list
       and this will tell you how many there are.

       Generally we should minimize those requirements as much as
       possible.

    """
    # Import this here because not all environments have pip.
    from pip.req import parse_requirements

    req_path = path('requirements')
    req_files = [os.path.join(req_path, fn) for fn in os.listdir(req_path)]

    reqs = list(chain(*(parse_requirements(path)
                        for path in req_files)))

    unsatisfied_reqs = []
    unsatisfyable_reqs = []
    for req in reqs:
        if req.url and 'github.com' in req.url:
            unsatisfyable_reqs.append(req)
            continue

        req.check_if_exists()

        if not req.satisfied_by:
            unsatisfied_reqs.append(req)

    if unsatisfyable_reqs:
        print 'There are %d requirements that cannot be checked.' % (
            len(unsatisfyable_reqs))

    if unsatisfied_reqs:
        print 'The following requirements are not satsifed:'
        print ''

        for req in unsatisfied_reqs:
            print 'UNSATISFIED:', req.req

        print ''
        print 'Update your virtual environment by doing:'
        print ''
        print '    ./peep install -r requirements/requirements.txt'
        print ''
        print 'or run with SKIP_CHECK=1 .'
        sys.exit(1)


def setup_environ(manage_file):
    """Sets up a Django app within a manage.py file"""
    # sys is global to avoid undefined local
    global sys, current_settings, execute_from_command_line, ROOT

    ROOT = os.path.dirname(os.path.abspath(manage_file))

    # Adjust the python path and put local packages in front.
    prev_sys_path = list(sys.path)

    # Make root application importable without the need for
    # python setup.py install|develop
    sys.path.append(ROOT)

    # FIXME: This is vendor/-specific. When we ditch vendor/ we can
    # ditch this.

    # Check for ~/.virtualenvs/fjordvagrant/. If that doesn't exist, then
    # launch all the vendor/ stuff.
    possible_venv = os.path.expanduser('~/.virtualenvs/fjordvagrant/')
    if not os.path.exists(possible_venv):
        os.environ['USING_VENDOR'] = '1'
        site.addsitedir(path('vendor'))

        # Move the new items to the front of sys.path. (via virtualenv)
        new_sys_path = []
        for item in list(sys.path):
            if item not in prev_sys_path:
                new_sys_path.append(item)
                sys.path.remove(item)
        sys.path[:0] = new_sys_path

    from django.core.management import execute_from_command_line  # noqa

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


def _not_setup():
    raise EnvironmentError(
        'setup_environ() has not been called for this process')


def main(argv=None):
    if current_settings is None:
        _not_setup()
    argv = argv or sys.argv
    execute_from_command_line(argv)
