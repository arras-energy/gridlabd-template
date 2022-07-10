#!/bin/bash

set -x
set -e

for TEMPLATE in $(cat $2/.index); do
    GLMNAME=$(basename "$1")
    DIRNAME=${GLMNAME/.glm/}
    CHECKDIR="$2/$TEMPLATE/$(dirname "$1")/$DIRNAME"
    if [ -d "$CHECKDIR" ]; then
        TESTDIR=test/$CHECKDIR
        mkdir -p "$TESTDIR"
        cp "$1" $CHECKDIR/autotest.* "$TESTDIR"
        cd "$TESTDIR"
        AUTOTESTGLM=$(find . -name autotest.glm -type f -print)
        gridlabd template get "$TEMPLATE" 1>stdout 2>stderr
        gridlabd "$GLMNAME" $AUTOTESTGLM -t "$TEMPLATE" --redirect all 1>>stdout 2>>stderr
        ok="OK"
        for FILE in $(find "$CHECKDIR" -type f -print); do
            if [ ! "$(basename $FILE)" == "autotest" ]; then
                diff "$FILE" $(basename "$FILE") >> gridlabd.diff || ok="FAIL"
            fi
        done
        echo $1: $ok
    fi
done
