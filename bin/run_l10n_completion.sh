#!/bin/bash

# Run this from the project root--not this directory!
#
# Usage: ./bin/run_l10n_completion.sh [PYTHON-BIN]

function usage() {
    echo "syntax: ./bin/run_l10n_completion.sh WEBAPP-DIR PYTHON-BIN"
    exit 1
}

if [[ $# -lt 2 ]]; then
    echo "Not enough arguments."
    usage
fi

WEBAPP=$1
PYTHONBIN=$2

# check if file and dir are there
if [[ ! -f "$PYTHONBIN" ]]; then
    echo "$PYTHONBIN does not exist."
    usage
fi

# Update .po files in svn
cd $WEBAPP/locale && svn up && cd $WEBAPP

# Run l10n completion to calculate percent completed and update .json
# file; keep 90 days of data
$PYTHONBIN $WEBAPP/bin/l10n_completion.py --truncate 90 $WEBAPP/media/l10n_completion.json $WEBAPP/locale/

echo 'Complete.'
ls -l $WEBAPP/media/l10n_completion.json
exit 1
