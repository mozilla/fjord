# First we import absolute imports from the future, so that our celery.py
# module will not clash with the library
from __future__ import absolute_import

import os
import site
import sys

from fjord.manage_utils import monkeypatch


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fjord.settings')


# Denotes that setup_vendor_path has been run.
_has_setup_vendor_path = False


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def path(*a):
    return os.path.join(ROOT, *a)


def setup_vendor_path():
    """Sets up path and vendor/ stuff"""
    global _has_setup_vendor_path

    if _has_setup_vendor_path:
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

    _has_setup_vendor_path = True


setup_vendor_path()

monkeypatch()


# Setup celery
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app
