# This file gets run by ./manage.py (runserver|test) and also gets
# imported for the WSGI application building by wsgi/playdoh.wsgi
# for stage/prod.
#
# It holds the setup that's common to both environments.

import os

import django
from django.core.handlers.wsgi import WSGIHandler

from fjord.wsgi_utils import BetterDebugMixin


os.environ.setdefault('CELERY_LOADER', 'django')


class DebuggableWSGIHandler(BetterDebugMixin, WSGIHandler):
    pass


def get_debuggable_wsgi_application():
    # This does the same thing as
    # django.core.wsgi.get_wsgi_application except it returns a
    # different WSGIHandler.
    django.setup()
    return DebuggableWSGIHandler()


application = get_debuggable_wsgi_application()
