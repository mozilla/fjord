"""This module holds all the functions that deal with starting up
Fjord for both the developer and server environments.

These functions shouldn't be used after startup is completed.

"""
import logging
import os
import site
import sys
from itertools import chain


log = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Denotes that setup_environ has been run.
_has_setup_environ = False

# Prevent from patching twice.
_has_patched = False


def path(*a):
    return os.path.join(ROOT, *a)


# Taken from peep
class EmptyOptions(object):
    """Fake optparse options for compatibility with pip<1.2

    pip<1.2 had a bug in parse_requirments() in which the ``options``
    kwarg was required. We work around that by passing it a mock
    object.

    """
    default_vcs = None
    skip_requirements_regex = None
    isolated_mode = False


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
    from pip.download import PipSession

    req_path = path('requirements')
    req_files = [os.path.join(req_path, fn) for fn in os.listdir(req_path)]

    reqs = list(chain(*(parse_requirements(path,
                                           options=EmptyOptions(),
                                           session=PipSession())
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
        print '    ./peep.sh install -r requirements/requirements.txt'
        print '    ./peep.sh install -r requirements/compiled.txt'
        print '    ./peep.sh install -r requirements/dev.txt'
        print ''
        print 'or run with SKIP_CHECK=1 .'
        sys.exit(1)


def setup_environ():
    """Sets up the Django environment

    1. sets up path and vendor/ stuff
    2. validates settings
    3. sets up django-celery

    """
    global _has_setup_environ

    if _has_setup_environ:
        return

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

    from django.conf import settings
    validate_settings(settings)

    import djcelery
    djcelery.setup_loader()

    _has_setup_environ = True


def validate_settings(settings):
    """Raise an error if we see insecure or missing settings"""
    from django.core.exceptions import ImproperlyConfigured

    if not settings.DATABASES['default']:
        msg = 'DATABASES["default"] needs to be set.'
        raise ImproperlyConfigured(msg)

    if not getattr(settings, 'SECRET_KEY', None):
        msg = 'settings.SECRET_KEY needs to be set.'
        raise ImproperlyConfigured(msg)

    if not settings.DEBUG:
        if not getattr(settings, 'SECRET_KEY', 'notsecret'):
            msg = 'settings.SECRET_KEY is set to "notsecret". please change.'
            raise ImproperlyConfigured(msg)

        if getattr(settings, 'SESSION_COOKIE_SECURE', None) is None:
            msg = (
                'settings.SESSION_COOKIE_SECURE should be set to True; '
                'otherwise, your session ids can be intercepted over HTTP!'
            )
            raise ImproperlyConfigured(msg)

        hmac = getattr(settings, 'HMAC_KEYS', {})
        if not len(hmac.keys()):
            msg = 'settings.HMAC_KEYS cannot be empty.'
            raise ImproperlyConfigured(msg)


def monkeypatch():
    """All the monkeypatching we have to do to get things running"""
    global _has_patched
    if _has_patched:
        return

    # Import for side-effect: configures logging handlers.
    from fjord.settings.log_settings import noop
    noop()

    # Monkey-patch admin site.
    from django.contrib import admin
    from django.contrib.auth.decorators import login_required
    from session_csrf import anonymous_csrf
    from adminplus.sites import AdminSitePlus

    # Patch the admin
    admin.site = AdminSitePlus()
    admin.site.login = login_required(anonymous_csrf(admin.site.login))

    # Monkey-patch django forms to avoid having to use Jinja2's |safe
    # everywhere.
    import jingo.monkey
    jingo.monkey.patch()

    # Monkey-patch Django's csrf_protect decorator to use
    # session-based CSRF tokens.
    import session_csrf
    session_csrf.monkeypatch()

    from jingo import load_helpers
    load_helpers()

    logging.debug("Note: monkeypatches executed in %s" % __file__)

    # Prevent it from being run again later.
    _has_patched = True


def main(argv=None):
    if not _has_setup_environ:
        raise EnvironmentError(
            'setup_environ() has not been called for this process')

    from django.core.management import execute_from_command_line

    argv = argv or sys.argv
    execute_from_command_line(argv)
