#!/bin/bash
#
# Syntax: ./update_results.sh TEMPLATE
#
# Update test result files in autotest/models folders of TEMPLATE
#

#set -x

if [ $# -eq 0 ]; then
	echo "Syntax: $(basename $0) TEMPLATE"
	exit 1
fi

for CSV in $(ls -1 test/*/*/*/$1/autotest/models/gridlabd-4/*/*/*.csv 2>/dev/null); do
	DST="${CSV/test\//}"
	if [ ! -f "$DST" -o "$CSV" -nt "$DST" ]; then
		echo -n "Updating $DST... "
		cp "$CSV" "$DST"
		echo "ok"
	fi
done
