#!/bin/bash
#
# Syntax: update.sh TEMPLATE [FOLDER]
#
# Update test result files in autotest/models folders of TEMPLATE
#

if [ $# -lt 1 -o ! -d "$1/autotest" ]; then
	echo "Syntax: $0 TEMPLATE"
	exit 1
fi
ROOT=$PWD
make models
gridlabd template get $(basename $1)
cd $1/autotest/models/gridlabd-4
for DIR in $(find . -type d -print | grep "$2" ); do
	echo Processing $DIR...
	if [ -f "$DIR/autotest.glm" ]; then
		( cd $DIR ; gridlabd $ROOT/autotest/models/gridlabd-4/$DIR.glm autotest.glm -t $(basename $1) --redirect all )
	fi
done
cd - >/dev/null
