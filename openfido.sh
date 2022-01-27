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
# default values for certain variables
MODEL_NAME_INPUT="model.glm"
OUTPUT_NAME_INPUT="output.csv"
START_TIME_INPUT="2020-01-01 00:00:00 PST"
STOP_TIME_INPUT="2020-01-01 12:00:00 PST"
TIME_ZONE_INPUT="PST+8PDT"

# no default values
TARIFF_ROW_INPUT=""
WEATHER_STATION=""


# rows can be in any order
while IFS=, read -r field1 field2
do
    case "$field1" in
        "WEATHER_STATION")
            WEATHER_STATION=$field2
            echo "$WEATHER_STATION"
            ;;
        "STARTTIME")
            START_TIME_INPUT=$field2
            echo "$START_TIME_INPUT"
            ;;
        "STOPTIME")
            STOP_TIME_INPUT=$field2
            echo "$STOP_TIME_INPUT"
            ;;
        "TIMEZONE")
            TIME_ZONE_INPUT=$field2
            echo "$TIME_ZONE_INPUT"
            ;;
        "TARIFF_INDEX")
            TARIFF_ROW_INPUT=$field2
            echo "$TARIFF_ROW_INPUT"
            ;;
        "MODEL")
            MODEL_NAME_INPUT=$field2
            echo "$MODEL_NAME_INPUT"
            ;;
        "OUTPUT")
            OUTPUT_NAME_INPUT=$field2
            echo "$OUTPUT_NAME_INPUT"
            ;;
        *)
            echo "$field1 8 $field2"
    
    esac
done < config.csv


echo "Running gridlabd" 

# put -t to get template online
gridlabd model.glm tariff_design.glm

mv output.csv $OPENFIDO_OUTPUT

exit 0
