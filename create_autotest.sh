#!/bin/bash
#
# Syntax: ./create_autotest.sh TEMPLATE
# 
# Create autotests for a template
#

if [ $# -eq 0 ]; then
	echo "Syntax: $(basename $0) TEMPLATE"
	exit 1
fi

for SRC in $(ls -d1 autotest/models/gridlabd-4/*/*.glm 2>/dev/null); do
	DIR=${SRC/.glm/}
	for TEMPLATE in $(ls -d1 */*/*/$1); do 
		DST=$TEMPLATE/$DIR
		if [ ! -d $DIR ]; then
			echo "Creating $DST..."
			mkdir -p $DST
		fi
		GLM=$DST/autotest.glm
		if [ ! -f $GLM ]; then
			echo "Creating $GLM..."
			touch $GLM
		fi
	done
done
