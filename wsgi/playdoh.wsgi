# This gets used by stage/prod to set up the WSGI application for stage/prod
# use. We do some minor environment setup and then have `fjord/wsgi.py` do
# the rest.

import os
import site

# Set up NewRelic stuff.
try:
    import newrelic.agent
except ImportError:
    newrelic = False


if newrelic:
    newrelic_ini = os.getenv('NEWRELIC_PYTHON_INI_FILE', False)
    if newrelic_ini:
        newrelic.agent.initialize(newrelic_ini)
    else:
        newrelic = False


# Set the settings module explicitly if we don't have one in the
# environment already.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fjord.settings')

# Add the app dir to the python path so we can import manage.
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../')))

# Set up the environment and monkeypatch.
from fjord import manage_utils

manage_utils.setup_environ()
manage_utils.monkeypatch()

from fjord.wsgi import get_wsgi_application
application = get_wsgi_application()

if newrelic:
    application = newrelic.agent.wsgi_application()(application)
