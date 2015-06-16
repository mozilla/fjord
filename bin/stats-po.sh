#!/bin/bash

# syntax:
# stats-po.sh

echo "Printing number of untranslated strings found in locales:"

for lang in `find $1 -type f -name "django.po" | sort`; do
dir=`dirname $lang`
    stem=`basename $lang .po`
    count=$(msgattrib --untranslated $lang | grep -c "msgid")
    echo -e "$(dirname $dir)\t\tmain=$count"
done
