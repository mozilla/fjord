#!/usr/bin/env python
import os

# Edit this if necessary or override the variable in your environment.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fjord.settings')

from fjord import manage

manage.setup_environ(__file__)

from fjord.base import monkeypatches
monkeypatches.patch()


if __name__ == "__main__":
    manage.main()
