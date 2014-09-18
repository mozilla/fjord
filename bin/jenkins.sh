#!/bin/sh
# This script makes sure that Jenkins can properly run your tests against your
# codebase.
set -e

DB_HOST="localhost"
DB_USER="hudson"

cd $WORKSPACE
VENV=$WORKSPACE/venv

echo "Starting build on executor $EXECUTOR_NUMBER..."

# Make sure there's no old pyc files around.
find . -name '*.pyc' -exec rm {} \;

if [ ! -d "$VENV/bin" ]; then
  echo "No virtualenv found.  Making one..."
  virtualenv $VENV --no-site-packages
  source $VENV/bin/activate
  pip install --upgrade pip
  pip install coverage
fi

git submodule sync -q
git submodule update --init --recursive

if [ ! -d "$WORKSPACE/vendor" ]; then
    echo "No /vendor... crap."
    exit 1
fi

source $VENV/bin/activate
pip install -q -r requirements/compiled.txt

cat > fjord/settings/local.py <<SETTINGS
from fjord.settings.base import *

SECRET_KEY = 'pining'
LOG_LEVEL = logging.ERROR

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '${DB_HOST}',
        'NAME': '${JOB_NAME}',
        'USER': 'hudson',
        'PASSWORD': '',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
        'TEST_NAME': 'test_${JOB_NAME}',
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_general_ci',
    }
}

ES_URLS = ['http://jenkins-es:9200']
HMAC_KEYS = {'2012-06-06': 'jenkinsrocks'}

from django_sha2 import get_password_hashers
PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)
SETTINGS

echo "Creating database if we need it..."
echo "CREATE DATABASE IF NOT EXISTS ${JOB_NAME}"|mysql -u $DB_USER -h $DB_HOST

echo "Fetch product details..."
python manage.py update_product_details -f

echo "Generating all the static assets..."
python manage.py collectstatic --noinput
python manage.py compress_assets

echo "Starting tests..."
coverage run manage.py test -v 2 --noinput --with-xunit
coverage xml $(find fjord lib -name '*.py')

echo "FIN"
