#!/bin/bash

pip install --download=vendor/packages --no-use-wheel --src=vendor/src -I $@
echo "Go into vendor/packages/ and untar the new directories."
echo "Good luck!"
