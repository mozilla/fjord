#!/usr/bin/env python
import os
# Do this before *anything*.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fjord.settings')

from fjord import manage_utils


if __name__ == '__main__':
    # This has to get called after DJANGO_SETTINGS_MODULE stuff has
    # been sorted out.
    manage_utils.setup_environ()
    manage_utils.monkeypatch()

    SKIP_CHECK = os.environ.get('SKIP_CHECK', '0')
    USING_VENDOR = os.environ.get('USING_VENDOR', '0')

    if USING_VENDOR == '0' and SKIP_CHECK != '1':
        manage_utils.check_dependencies()

    manage_utils.main()
