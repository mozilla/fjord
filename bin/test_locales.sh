#!/bin/bash

# This creates a faux Pirate locale under xx and transforms all the
# strings such that every resulting string has four properties:
#
# 1. it's longer than the English equivalent (tests layout issues)
# 2. it's different than the English equivalent (tests missing gettext calls)
# 3, every string ends up with a non-ascii character (tests unicode)
# 4. looks close enough to the English equivalent that you can quickly
#    figure out what's wrong
# 5. it's kind of funny so it adds some lightness to the heavy hardships
#    of development toil
#
# Run this from the project root directory like this:
#
# $ bin/test_locales.sh

echo "extract and merge...."
./manage.py extract
./manage.py merge

echo "creating dir...."
mkdir -p locale/xx/LC_MESSAGES

echo "copying django.pot file...."
cp locale/templates/LC_MESSAGES/django.pot locale/xx/LC_MESSAGES/django.po

echo "translate django.po file...."
./manage.py translate --pipeline=html,pirate locale/xx/LC_MESSAGES/django.po
locale/compile-mo.sh locale/xx/
