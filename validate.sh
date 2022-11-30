#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Syntax: $(basename $0) [--debug] GLMNAME ORGANIZATION"
    exit 1
fi

if [ $1 == "--debug" ]; then
    set -x
    shift 1
fi

ROOTDIR=$PWD
result="OK"
for TEMPLATE in $(cat $2/.index); do
    GLMNAME="$(basename "$1")"
    DIRNAME="${GLMNAME/.glm/}"
    cd "$ROOTDIR"
    CHECKDIR="$2/$TEMPLATE/$(dirname "$1")/$DIRNAME"
    # if gridlabd template get "$TEMPLATE" 1>stdout 2>stderr; then
    #    echo "$TEMPLATE: template error $?" >> /dev/stderr
    # elif
    if [ -d "$CHECKDIR" ]; then
        TESTDIR="test/$CHECKDIR"
        mkdir -p "$ROOTDIR/$TESTDIR"
        cp "$1" $CHECKDIR/autotest.* "$TESTDIR"
        cd "$ROOTDIR/$TESTDIR"
        AUTOTESTGLM=$(find . -name autotest.glm -type f -print)
        err=""
        ok="OK"
        if gridlabd "$GLMNAME" "$AUTOTESTGLM" -t "$TEMPLATE" --redirect all 1>>stdout 2>>stderr; then
            err="gridlabd error $?"
        else
            for FILE in $(find "$ROOTDIR/$CHECKDIR" -type f -print); do
                TARGET=$(basename "$FILE")
                if [ ! "${TARGET%.*}" == "autotest" ]; then
                    if [ ! -f "$TARGET" ]; then
                        err="$CHECKDIR/$TARGET not found"
                    else
                        diff -w "$FILE" "$TARGET" >> gridlabd.diff || err="output $TARGET differs"
                    fi            
                fi
            done
        fi
        if [ ! -z "$err" ]; then
            result="FAIL"
            ok="FAIL"
            echo "$GLMNAME: $err" >/dev/stderr
        fi            
        echo "${CHECKDIR}: $ok"
    else
        echo "WARNING: $CHECKDIR not found" >/dev/stderr
    fi
done

if [ "$result" != "OK" ]; then
    exit 1
fi

exit 0