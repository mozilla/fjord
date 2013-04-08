"""
This is imported as the DJANGO_SETTINGS_MODULE. It imports local.py
which imports base.py which imports funfactory.settings_base.

Thus:

1. base.py overrides funfactory.settings_base
2. local.py overrides everything

"""

try:
    from fjord.settings.local import *
except ImportError as exc:
    exc.args = tuple(['%s (did you rename settings/local.py-dist?)' % exc.args[0]])
    raise exc
