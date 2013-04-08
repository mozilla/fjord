"""
This is imported as the DJANGO_SETTINGS_MODULE. It imports local.py
which imports base.py which imports funfactory.settings_base. Thus,
the override order is this:

* funfactory.settings_base     - funfactory defaults
* base.py                      - fjord defaults
* local.py                     - instance specific settings
"""

try:
    from fjord.settings.local import *
except ImportError as exc:
    exc.args = tuple(['%s (did you rename settings/local.py-dist?)' % exc.args[0]])
    raise exc
