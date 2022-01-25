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

if ! ls -1 $OPENFIDO_INPUT/*.glm; then
  echo "Input .glm file not found"
  exit 1
fi

if ! ls -1 $OPENFIDO_INPUT/*.csv; then
  echo "Input .csv file not found"
  exit 1
fi


# go to directory where the files are 
cd US/CA/SLAC/tariff_design

echo "Copying input files to working directory"
cp -r $OPENFIDO_INPUT/* .

while IFS=, read -r field1 field2
do
    echo "$field1 and $field2"
done < config.csv


echo "Running gridlabd" 

# put -t to get template online
gridlabd model.glm tariff_design.glm

mv output.csv $OPENFIDO_OUTPUT

exit 0
