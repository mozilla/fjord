import sys

# This is imported as the DJANGO_SETTINGS_MODULE. It imports local.py
# which imports base.py which imports funfactory.settings_base.
#
# Thus:
#
# 1. base.py overrides funfactory.settings_base
# 2. local.py overrides everything
# 3. if we're running tests, tests override local

try:
    from fjord.settings.local import *
except ImportError as exc:
    exc.args = tuple(['%s (did you rename settings/local.py-dist?)' % exc.args[0]])
    raise exc

print sys.argv

TEST = len(sys.argv) > 1 and sys.argv[1] == 'test'
if TEST:
    print 'TEST CONFIG'
    from fjord.settings.test import *
