# This file gets run by ./manage.py (runserver|test) and also gets
# imported for the WSGI application building by wsgi/playdoh.wsgi
# for stage/prod.
#
# It holds setup that's common to both environments.

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault('CELERY_LOADER', 'django')


application = get_wsgi_application()
