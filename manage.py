#!/usr/bin/env python
import os

# Edit this if necessary or override the variable in your environment.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fjord.settings')

from fjord import manage_utils

manage_utils.setup_environ(__file__)

from fjord.base import monkeypatches
monkeypatches.patch()


SKIP_CHECK = os.environ.get('SKIP_CHECK', '0')
USING_VENDOR = os.environ.get('USING_VENDOR', '0')


if USING_VENDOR == '0' and SKIP_CHECK != '1':
    manage_utils.check_dependencies()


if __name__ == "__main__":
    manage_utils.main()
