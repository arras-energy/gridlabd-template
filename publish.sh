#!/bin/bash

ORGS=$(grep -v '^#' .orgs)

for org in $ORGS; do
	cd $org
	INDEX=$(grep -v '^#' .index)
	for zip in $INDEX; do
		base=${zip/.zip/}
		echo "Updating $zip from $base..."
		if [ -f $zip ]; then
			zip -f $zip $base/*.*
		else
			zip $zip $base/*.*
		fi
	done
done