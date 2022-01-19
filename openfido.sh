#!/bin/sh


# nounset: undefined variable outputs error message, and forces an exit
set -u
# errexit: abort script at first error
set -e
# print command to stdout before executing it:
set -x

echo "hi"

echo "OPENFIDO_INPUT = $OPENFIDO_INPUT"
echo "OPENFIDO_OUTPUT = $OPENFIDO_OUTPUT"

# go to directory where the files are 
cd US/CA/SLAC/tariff_design

echo "Running gridlabd" 

# put -t to get the template online 
gridlabd model.glm tariff_design.glm >&1 | tee output.txt

cat output.txt 
mv output.txt $OPENFIDO_OUTPUT

exit 0
