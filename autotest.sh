#!/bin/bash

DIRLIST=$(find . -type d -name autotest -print)

for DIR in $DIRLIST; do
	cd $DIR
	TEMPLATE=$(cd ..;echo $(basename $PWD))
	echo Running $TEMPLATE in $PWD...
	for GLM in $(ls -1 *.glm); do
		if [ $GLM != "config.glm" ]; then
			echo -n "  $GLM..."
			gridlabd -D pythonpath=.. config.glm $GLM ../$TEMPLATE.glm
			echo "done"
		fi
	done
done