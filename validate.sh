#!/bin/bash
#
# validate.sh - Validate the templates in this repository
#
# Syntax: ./validate.sh [OPTIONS ...]
#
# Options
#   --debug    enable debug output
#   --quiet    disable standard output
#   --silent   disable error output
#   --verbose  echo all commands as they are executed
#   --warning  disable warning output
#
# The validate process generates the file validate.tar.gz when a failure is detected.
# The following outcomes are possible for each test case:
#
#   OK    the test succeeded
#   FAIL  the simulation run failed
#   DIFF  the simulation output did not match expected results
#
# The autotest files are stored in the `autotest` folder in each template. The folder
# tree matches the folder tree structure in the `autotest` folder.  The testing output
# is saved in the `test` folder. All CSV files in the autotest folder are checked
# against files in the `test` folder and differences are reported as test failures.
#

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

function record()
{
    echo $* >> "$VALIDATE"
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

VALIDATE=$ROOTDIR/validate.txt
echo "Validation process started $(date)" > "$VALIDATE"

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
    elif [ $1 == '--help' -o $1 == '-h' -o $1 == 'help' ]; then
        grep ^# validate.sh | tail -n +3 | cut -c3- | more
        exit 0
    else
        error 1 "option '$1' is invalid" 
    fi
    shift 1
done

TESTED=0
FAILED=0

for ORG in $(grep -v ^# ".orgs"); do
    debug "organization $ORG..."
    for TEMPLATE in $(cd $ORG; ls -dF1 * 2>/dev/null | grep '/$' | sed -e 's:/$::'); do
        debug "template $TEMPLATE..."
        if [ ! -d autotest ]; then
            warning "$ORG/$TEMPLATE has no autotest"
        else
            for AUTOTEST in $(cd "$ORG/$TEMPLATE" ; find * -name autotest.glm 2>/dev/null); do
                debug "AUTOTEST=$ORG/$TEMPLATE/$AUTOTEST"
                SOURCE=${AUTOTEST/\/autotest.glm/.glm}
                debug "SOURCE=$SOURCE"
                TESTDIR="test/${ORG}/${TEMPLATE}/${SOURCE/.glm/}"
                debug "TESTDIR=$TESTDIR"
                
                MODEL="${AUTOTEST/$TEMPLATE\/}"
                processing "$ORG/$TEMPLATE/$SOURCE"

                mkdir -p "$TESTDIR" || warning "unable to create $TESTDIR"
                rm -f "$TESTDIR"/* || warning "unable to cleanup $TESTDIR"

                cp "$SOURCE" "$TESTDIR" || warning "unable to copy $SOURCE to $TESTDIR"
                cp "$ORG/$TEMPLATE/$AUTOTEST" "$TESTDIR" || warning "unable to copy $AUTOTEST to $TESTDIR"

                if gridlabd -D pythonpath="$ROOTDIR/$ORG/$TEMPLATE" -W "$TESTDIR" autotest.glm $(basename "$SOURCE") -o gridlabd.json "$ROOTDIR/$ORG/$TEMPLATE/$TEMPLATE.glm" 1>"$TESTDIR/gridlabd.out" 2>&1; then
                    echo "[Success: exit code $?]" >> "$TESTDIR/gridlabd.out"
                    debug "Searching $(dirname $ORG/$TEMPLATE/$AUTOTEST) for check CSV files..."
                    DIFFER=0
                    for CHECKCSV in $(find $(dirname "$ORG/$TEMPLATE/$AUTOTEST") -name '*.csv' -print); do
                        debug "Checking $CHECKCSV..."
                        diff -w "$CHECKCSV" "$TESTDIR/$(basename $CHECKCSV)" 1>"$TESTDIR/gridlabd.diff" 2>/dev/null
                        if [ $? -ne 0 ]; then
                            DIFFER=$(($DIFFER+1))
                        fi
                    done
                    if [ $DIFFER -gt 0 ]; then
                        record "$AUTOTEST outputs differ"
                        status DIFF
                        FAILED=$(($FAILED+1))
                    else
                        record "$AUTOTEST ok"
                        status OK
                    fi
                else
                    echo "[Failed: exit code $?]" >> "$TESTDIR/gridlabd.out"
                    record "$AUTOTEST failed"
                    status FAIL
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
if [ $FAILED -gt 0 ]; then
    tar cfz validate.tar.gz test
    exit 1
else
    exit 0
fi


