#!/bin/bash

pip install --no-install --build=vendor/packages --no-use-wheel --src=vendor/src -I $@
