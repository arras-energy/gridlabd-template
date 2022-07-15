#!/bin/bash
#
# Syntax: update.sh [OPTIONS ...] TEMPLATE [FOLDER]
#
# Update test result files in autotest/models folders of TEMPLATE
#

if [ $# -lt 1 -o ! -d "$1/autotest" ]; then
	echo "Syntax: $0 [OPTIONS ...] TEMPLATE [FOLDER]"
	exit 1
elif [ "$1" == "help" -o "$1" == "-h" -o "$1" == "--help" ]; then
	echo "Syntax: $0 [OPTIONS ...] TEMPLATE [FOLDER]"
	echo "Options:"
	echo "  --debug          show commands as they are executed"
	echo "  --get_template   get the template from the configure template repository"
	echo "  --help|-h|help   show this help"
	exit 0
fi

while [ "${1:0:1}" == '-' ]; do
	if [ "$1" == "--get-template" ]; then
		gridlabd template get $(basename $1)
	elif [ "$1" == "--debug" ]; then
		set -x
	else
		echo "ERROR [$0]: option '$1' is invalid"
	fi
done

ROOT=$PWD
make models
cd $1/autotest/models/gridlabd-4
for DIR in $(find . -type d -print | grep "$2" ); do
	echo Processing ${DIR/./$ROOT/$1/autotest/models/gridlabd-4}...
	if [ -f "$DIR/autotest.glm" ]; then
		( cd $DIR ; gridlabd $ROOT/autotest/models/gridlabd-4/$DIR.glm autotest.glm -t $(basename $1) --redirect all 1>stdout 2>stderr)
		EXITCODE=$?
		if [ $EXITCODE -ne 0 ]; then
			echo "ERROR [$(basename $0)]: test '${DIR:2}' run failed (exit code $EXITCODE)"
		fi
	fi
done
cd - >/dev/null
