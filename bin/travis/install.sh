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

if [[ $TEST_SETUP == "minimal" ]]; then
    exit 0
fi

echo "Installing Node.js dependencies"
npm install > /dev/null 2> /dev/null
npm list
echo

echo "Installing ElasticSearch"
ES_TARBALL="vendor/tarballs/elasticsearch-${ELASTICSEARCH_VERSION}.tar.gz"
if [[ ! -f "${ES_TARBALL}" ]]; then
    echo "Invalid version of Elasticsearch. Can't find ${ES_TARBALL}."
    exit 1
fi
tar xzvf "${ES_TARBALL}" > /dev/null
