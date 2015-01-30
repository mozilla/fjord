#!/bin/bash
# pwd is the git repo.
set -e

echo "Install Python dependencies"
./peep.sh install \
    -r requirements/compiled.txt \
    -r requirements/requirements.txt \
    -r requirements/dev.txt

# Print the installed packages for the world to see.
pip freeze
echo

echo "Installing Node.js dependencies"
npm install > /dev/null 2> /dev/null
npm list
echo

echo "Installing ElasticSearch"
tar xzvf vendor/tarballs/elasticsearch-0.90.10.tar.gz > /dev/null
