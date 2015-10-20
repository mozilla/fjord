#!/bin/bash

# Run this from the project root--not from this directory!
#
# usage: compile-linted-mo.sh [-p <PYTHON>]

function compilemo() {
    dir=`dirname $1`
    stem=`basename $1 .po`

    target="${dir}/${stem}.mo"
    targettmp="${dir}/${stem}.mo.tmp"

    echo "Compiling $1..."

    # Run msgfmt which will compile the .mo file
    msgfmt --check-header -o "${targettmp}" "$1"

    # If msgfmt returned a zero exit code, then everything is fine and copy
    # the .mo file to the final destination
    if [ $? -eq 0 ]
    then
        mv "${targettmp}" "${target}"
    fi
}

# Get the path to the python binary from the "-p <PYTHON>"
# arg or default to "python2.6".
if [ "$1" = "-p" ]
then
    PYTHON="$2"
else
    PYTHON="python"
fi

NO_MO_FILES=();
GOOD_FILES=();
BAD_FILES=();

for pofile in `find locale/ -name "*.po"`
do
    dir=`dirname $pofile`
    stem=`basename $pofile .po`

    # If no .mo file exists, we compile it. If it does exist, then we
    # lint the .po file and only compile to .mo if it's error-free.
    if [ ! -e "${dir}/${stem}.mo" ]
    then
        compilemo $pofile
        NO_MO_FILES+=("${pofile}")

    else
        "${PYTHON}" manage.py lint --errorsonly "${pofile}"
        if [ $? -ne 0 ]
        then
            BAD_FILES+=("${pofile}")

        else
            compilemo $pofile
            GOOD_FILES+=("${pofile}")
        fi
    fi
done

for pofile in ${NO_MO_FILES[@]}
do
    echo "NO MO FILE: ${pofile}"
done

for pofile in ${BAD_FILES[@]}
do
    echo "BUSTED: ${pofile}"
done

for pofile in ${GOOD_FILES[@]}
do
    echo "COMPILED: ${pofile}"
done
