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
while IFS=, read -r field1 field2 || [ -n "$field1" ]
do
    case "$field1" in
        "WEATHER_STATION")
            #set up variable
            WEATHER_STATION=$field2
            WEATHER_STATION_LIST=$(gridlabd weather index $WEATHER_STATION)
            if [ $(echo $WEATHER_STATION_LIST | wc -l) == 1 ] ; then
                WEATHER_STATION=$(basename $WEATHER_STATION_LIST .tmy3)
                echo $WEATHER_STATION
            fi
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
            echo "$field1 must be one of the following: WEATHER_STATION, START_TIME_INPUT, STOPTIME, TIMEZONE, TARIFF_INDEX, MODEL, OUTPUT"
            ;;
    
    esac
done < config.csv

#check variables to see if the ones that don't have a default are updated

#I'll make it into a temporary csv file and then run a python script to format it


echo "Running gridlabd" 

# put -t to get template online
gridlabd $MODEL_NAME_INPUT tariff_design.glm
if [ $OUTPUT_NAME_INPUT != "output.csv" ]; then
  mv output.csv $OUTPUT_NAME_INPUT
fi

mv $OUTPUT_NAME_INPUT $OPENFIDO_OUTPUT

exit 0
