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

echo "This is output: $(gridlabd US/CA/SLAC/tariff-design/model.glm US/CA/SLAC/tariff-design/tariff-design.glm)"

echo "hi"

exit 0
