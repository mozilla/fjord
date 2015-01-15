#!/bin/bash

SUITE=${1:-all}

case $SUITE in
    all )
        bin/travis/test.sh
        ;;
    django )
        bin/travis/test.sh
        ;;
    * )
        echo "Unknown test suite '$SUITE'."
        exit 1
esac
