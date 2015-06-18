#!/bin/bash
# pwd is the git repo.
set -e

echo "Creating settings/local.py"
cp fjord/settings/travis.py-dist fjord/settings/local.py

echo "Creating test database"
mysql -e 'CREATE DATABASE fjord CHARACTER SET utf8 COLLATE utf8_unicode_ci;'

if [[ $TEST_SETUP == "minimal" ]]; then
    exit 0
fi

# Start Elasticsearch first to give it time to fully start up before
# the tests run.
echo "Starting Elasticsearch"
pushd "elasticsearch-${ELASTICSEARCH_VERSION}"
# Elasticsearch 0.90.10 daemonizes by default. Other versions require
# -d to be passed.
if [[ "${ELASTICSEARCH_VERSION}" == "0.90.10" ]]; then
    ./bin/elasticsearch
else
    ./bin/elasticsearch -d
fi
popd

echo "Updating product details"
python manage.py update_product_details

echo "Doing static dance"
python manage.py collectstatic --noinput > /dev/null
