"""This module holds all the functions that deal with starting up
Fjord for both the developer and server environments.

These functions shouldn't be used after startup is completed.

"""
import logging
import os
import sys
from functools import wraps
from itertools import chain

from fjord import path


log = logging.getLogger(__name__)

# Denotes that setup_environ has been run
_has_setup_environ = False

# Prevent from patching twice
_has_patched = False


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
        if req.link and req.url and 'github.com' in req.url:
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

    1. validates settings
    2. sets up django-celery

    """
    global _has_setup_environ

    if _has_setup_environ:
        return

    from django.conf import settings
    validate_settings(settings)

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

    # Import for side-effect: configures logging handlers
    from fjord.settings.log_settings import noop
    noop()

    # Monkey-patch admin site
    from django.contrib import admin
    from django.contrib.auth.decorators import login_required
    from session_csrf import anonymous_csrf
    from adminplus.sites import AdminSitePlus

    # Patch the admin
    admin.site = AdminSitePlus()
    admin.site.login = login_required(anonymous_csrf(admin.site.login))

    # Monkey-patch Django's csrf_protect decorator to use
    # session-based CSRF tokens
    import session_csrf
    session_csrf.monkeypatch()

    logging.debug('Note: monkeypatches executed in %s' % __file__)

    # Prevent it from being run again later
    _has_patched = True


def monkeypatch_render():
    """Monkeypatches django.shortcuts.render for Jinja2 kung-fu action

    .. Note::

       Only call this in a testing context!

    """
    import django.shortcuts

    def more_info(fun):
        """Django's render shortcut, but captures information for testing

        When using Django's render shortcut with Jinja2 templates, none of
        the information is captured and thus you can't use it for testing.

        This alleviates that somewhat by capturing some of the information
        allowing you to test it.

        Caveats:

        * it does *not* capture all the Jinja2 templates used to render.
        Only the topmost one requested by the render() function.

        """
        @wraps(fun)
        def _more_info(request, template_name, *args, **kwargs):
            resp = fun(request, template_name, *args, **kwargs)

            resp.jinja_templates = [template_name]
            if args:
                resp.jinja_context = args[0]
            elif 'context' in kwargs:
                resp.jinja_context = kwargs['context']
            else:
                resp.jinja_context = {}

            return resp
        return _more_info

    django.shortcuts.render = more_info(django.shortcuts.render)


def main(argv=None):
    if not _has_setup_environ:
        raise EnvironmentError(
            'setup_environ() has not been called for this process')

    from django.core.management import execute_from_command_line

    argv = argv or sys.argv
    execute_from_command_line(argv)
