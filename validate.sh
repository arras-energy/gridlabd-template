#!/bin/bash

if [ $1 == "--debug" ]; then
    set -x
    shift 1
fi

ROOTDIR=$PWD
result="OK"
for TEMPLATE in $(cat $2/.index); do
    GLMNAME=$(basename "$1")
    DIRNAME=${GLMNAME/.glm/}
    cd $ROOTDIR
    CHECKDIR="$2/$TEMPLATE/$(dirname "$1")/$DIRNAME"
    if [ -d "$CHECKDIR" ]; then
        TESTDIR=test/$CHECKDIR
        mkdir -p "$ROOTDIR/$TESTDIR"
        cp "$1" $CHECKDIR/autotest.* "$TESTDIR"
        cd "$ROOTDIR/$TESTDIR"
        AUTOTESTGLM=$(find . -name autotest.glm -type f -print)
        gridlabd template config set GITUSER $(basename $(dirname $(git rev-parse --show-toplevel)))
        gridlabd template config set GITREPO $(basename $(git rev-parse --show-toplevel))
        gridlabd template config set GITBRANCH $(git rev-parse --abbrev-ref HEAD)
        gridlabd template get "$TEMPLATE" 1>stdout 2>stderr
        gridlabd "$GLMNAME" $AUTOTESTGLM -t "$TEMPLATE" --redirect all 1>>stdout 2>>stderr
        ok="OK"
        for FILE in $(find $ROOTDIR/$CHECKDIR -type f -print); do
            TARGET=$(basename "$FILE")
            if [ ! "${TARGET%.*}" == "autotest" ]; then
                if [ ! -f "$TARGET" ]; then
                    echo "ERROR: '$CHECKDIR/$TARGET' not found" > /dev/stderr
                else
                    diff -w "$FILE" "$TARGET" >> gridlabd.diff || ok="FAIL"
                    if [ "$ok" == "FAIL" ]; then
                        result="FAIL"
                        echo "ERROR: '$CHECKDIR/$TARGET' is different" >/dev/stderr
                    fi
                fi
            fi
        done
        echo ${CHECKDIR/autotest\/models\/gridlabd-4/...}/$TARGET: $ok
    fi
done

if [ "$result" != "OK" ]; then
    exit 1
fi

exit 0