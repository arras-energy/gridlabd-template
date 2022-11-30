#!/bin/bash

set -u

BASENAME="$(basename $0)"
cd "$(dirname $0)"
ROOTDIR=$PWD

function warning()
{
    [ $WARNING == yes ] && echo "WARNING [$BASENAME]: $*"> /dev/stderr
}

function error()
{
    XC=$1
    shift 1
    [ $SILENT == no ] && echo "ERROR [$BASENAME]: $2 (exit code $XC)" > /dev/stderr
    exit $XC
}

function output()
{
    [ $QUIET == no ] && echo $*
}

function processing()
{
    [ $QUIET == no ] && echo -n "Processing $*..." > /dev/stderr
}

function status()
{
    [ $QUIET == no ] && echo " $*"> /dev/stderr
}

function debug()
{
    [ $DEBUG == yes ] && echo "DEBUG [$BASENAME]: $*"> /dev/stderr
}

DEBUG=no
QUIET=no
SILENT=no
WARNING=yes

TEMPLATES=$(gridlabd --version=install)/share/gridlabd/template
VALIDATE=$ROOTDIR/validate.txt
echo "Validation process started $(date)" > $VALIDATE

while [ $# -gt 0 ]; do
    if [ $1 == '--verbose' ]; then
        set -x
    elif [ $1 == '--debug' ]; then
        DEBUG=yes
    elif [ $1 == '--quiet' ]; then
        QUIET=yes
    elif [ $1 == '--silent' ]; then
        SILENT=yes
    elif [ $1 == '--warning' ]; then
        WARNING=no
    else
        error 1 "option '$1' is invalid" 
    fi
    shift 1
done

TESTED=0
FAILED=0

for ORG in $(grep -v ^# ".orgs"); do
    debug "organization $ORG..."
    for TEMPLATE in $(cd $ORG ; find * -type d -print -prune); do
        if [ -d $TEMPLATES/$TEMPLATE ]; then
            gridlabd get ${TEMPLATE} || error 2 "gridlabd template get ${TEMPLATE} failed"
        fi
        debug "template $TEMPLATE..."
        if [ ! -d autotest ]; then
            warning "$ORG/$TEMPLATE has no autotest"
        else
            for AUTOTEST in $(cd $ORG/$TEMPLATE ; find * -name autotest.glm 2>/dev/null); do
                debug AUTOTEST=$ORG/$TEMPLATE/$AUTOTEST
                SOURCE=${AUTOTEST/\/autotest.glm/.glm}
                debug SOURCE=$SOURCE
                TESTDIR=test/${ORG}/${TEMPLATE}/${SOURCE/.glm/}
                debug TESTDIR=$TESTDIR
                
                MODEL=${AUTOTEST/$TEMPLATE\/}
                processing $ORG/$TEMPLATE/$SOURCE

                mkdir -p $TESTDIR || warning "unable to create $TESTDIR"
                rm -f $TESTDIR/* || warning "unable to cleanup $TESTDIR"

                cp $SOURCE $TESTDIR || warning "unable to copy $SOURCE to $TESTDIR"
                cp $ORG/$TEMPLATE/$AUTOTEST $TESTDIR || warning "unable to copy $AUTOTEST to $TESTDIR"

                if gridlabd -W $TESTDIR autotest.glm $(basename $SOURCE) -o gridlabd.json -t $TEMPLATE 1>$TESTDIR/gridlabd.out 2>&1; then
                    echo "[Success: exit code $?]" >> $TESTDIR/gridlabd.out
                    output "$AUTOTEST ok" >> $VALIDATE
                    status OK
                else
                    echo "[Failed: exit code $?]" >> $TESTDIR/gridlabd.out
                    output "$AUTOTEST failed" >> $VALIDATE
                    status FAILED
                    FAILED=$(($FAILED+1))
                fi
                TESTED=$(($TESTED+1))
            done
        fi
    done
done

echo "$TESTED tested"
echo "$FAILED failed"
[ $TESTED -eq 0 ] && echo "0% success" || echo "$((100-100*$FAILED/$TESTED))% success"

[ $FAILED -gt 0 ] && tar cfz validate.tar.gz test
