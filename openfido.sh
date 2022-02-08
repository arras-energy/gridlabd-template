#!/bin/sh


# nounset: undefined variable outputs error message, and forces an exit
set -u
# errexit: abort script at first error
set -e
# print command to stdout before executing it:
set -x

echo "OPENFIDO_INPUT = $OPENFIDO_INPUT"
echo "OPENFIDO_OUTPUT = $OPENFIDO_OUTPUT"

if ! ls -1 $OPENFIDO_INPUT/*.glm; then
  echo "Input .glm file not found"
  exit 1
fi

if ! ls -1 $OPENFIDO_INPUT/config.csv; then
  echo "Input config.csv file not found"
  exit 1
fi


# go to directory where the files are 
cd US/CA/SLAC/tariff_design

echo "Copying input files to working directory"
cp -r $OPENFIDO_INPUT/* .
# default values for certain variables
MODEL_NAME_INPUT="model.glm"
OUTPUT_NAME_INPUT="output.csv"

# no default values
WEATHER_STATION=""

python3 csv_prepare.py 

if ls error.csv; then
  echo "Error with tariff information in config.csv."
  mv error.csv $OPENFIDO_OUTPUT
  exit 0
fi
# rows can be in any order
while IFS=, read -r field1 field2 || [ -n "$field1" ]
do
    case "$field1" in
        "WEATHER_STATION")
            # TODO: handle if input doesn't return a unique weather station
            # Replaces weather station with correctly formatted weather station
            WEATHER_STATION=$field2
            WEATHER_STATION_LIST=$(gridlabd weather index $WEATHER_STATION)
            ;;
        "MODEL")
            MODEL_NAME_INPUT=$field2
            echo "$MODEL_NAME_INPUT"
            ;;
        "OUTPUT")
            OUTPUT_NAME_INPUT=$field2
            echo "$OUTPUT_NAME_INPUT"
            ;;
    esac
done < config.csv

if [ $(echo $WEATHER_STATION_LIST | wc -l) == 1 ] ; then
    WEATHER_STATION_PARSED=$(basename $WEATHER_STATION_LIST .tmy3)
    echo "$WEATHER_STATION"
    echo "$WEATHER_STATION_PARSED"
    gawk -i inplace -F ',' '{gsub(find,replace,$2); print}' find="$WEATHER_STATION" replace="$WEATHER_STATION_PARSED" OFS="," config.csv
    echo $(cat config.csv)
fi



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
