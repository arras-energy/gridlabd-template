#!/bin/bash

ORGS=$(grep -v '^#' .orgs)

for org in $ORGS; do
	cd $org
	INDEX=$(grep -v '^#' .index)
	for zip in $INDEX; do
		base=${zip/.zip/}
		(cd $base ; zip ../$zip *.*)
	done
done