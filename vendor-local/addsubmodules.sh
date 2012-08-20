#!/bin/bash
for f in vendor-local/src/*; do
    pushd $f > /dev/null && REPO=$(git config remote.origin.url) && popd > /dev/null && git submodule add $REPO $f
done
