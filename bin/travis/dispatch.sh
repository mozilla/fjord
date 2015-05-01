#!/bin/bash

SUITE=${1:-all}

case $SUITE in
    django )
        bin/travis/test.sh
        ;;
    djangocheck )
        bin/travis/djangocheck.sh
        ;;
    * )
        echo "Unknown test suite '$SUITE'."
        exit 1
esac
