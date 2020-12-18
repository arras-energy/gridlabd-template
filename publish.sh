#!/bin/bash

ORGS=$(grep -v '^#' .orgs)

for org in $ORGS; do
	cd $org
	INDEX=$(grep -v '^#' .index)
	for zip in $INDEX; do
		base=${zip/.zip/}
		if [ -f $zip ]; then
			(cd $base ; zip -f ../$zip *.*)
		else
			(cd $base ; zip ../$zip *.*)
		fi
	done
done