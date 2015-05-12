#!/bin/bash
# pwd is the git repo.
set -e

python manage.py test \
  --noinput --logging-clear-handlers \
  --with-nicedots \
  --with-blockage
echo 'Booyahkasha!'
