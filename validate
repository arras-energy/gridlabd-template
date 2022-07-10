#!/bin/bash
set -x
set -e

for TEMPLATE in $(cat $2/.index); do
    GLMNAME=$(basename "$1")
    DIRNAME=${GLMNAME/.glm/}
    TESTDIR=test/$(dirname "$1")/$DIRNAME/$2/$TEMPLATE
    echo "Testing $TESTDIR/$GLMNAME..."
    mkdir -p "$TESTDIR"
    cp "$1" "$TESTDIR"
    cd "$TESTDIR"
    gridlabd template get "$TEMPLATE" 1>stdout 2>stderr
    gridlabd "$GLMNAME" -t "$TEMPLATE" --redirect all 1>>stdout 2>>stderr
done
