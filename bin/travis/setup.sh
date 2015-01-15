#!/bin/bash
# pwd is the git repo.
set -e

echo "Creating settings/local.py"
cp fjord/settings/travis.py-dist fjord/settings/local.py

echo "Creating test database"
mysql -e 'CREATE DATABASE fjord CHARACTER SET utf8 COLLATE utf8_unicode_ci;'

echo "Updating product details"
python manage.py update_product_details

echo "Starting ElasticSearch"
pushd elasticsearch-0.90.10
  # This will daemonize
  ./bin/elasticsearch
popd

echo "Doing static dance."
./manage.py collectstatic --noinput > /dev/null
./manage.py compress_assets > /dev/null
