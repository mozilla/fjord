import sys

# This is imported as the DJANGO_SETTINGS_MODULE. It imports local.py
# which imports base.py.
#
# Thus:
#
# 1. base.py has the defaults
# 2. local.py overrides everything
# 3. if we're running tests, tests override local

try:
    from fjord.settings.local import *
except ImportError as exc:
    exc.args = tuple(['%s (did you rename settings/local.py-dist?)' % exc.args[0]])
    raise exc


TEST = [arg for arg in sys.argv if 'py.test' in arg]
if TEST:
    print 'Using test settings'
    from fjord.settings.test import *
