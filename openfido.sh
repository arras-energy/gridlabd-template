#!/bin/sh


# nounset: undefined variable outputs error message, and forces an exit
set -u
# errexit: abort script at first error
set -e
# print command to stdout before executing it:
set -x
# later, get the value and put it back
# gridlabd -D suppress_repeat_messages=FALSE

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
WEATHER_STATION_INDEX_NUMBER=0

python3 -m pip install -r  requirements.txt
python3 csv_prepare.py 

if [ $? != 0 ];
then
    exit 1 
fi

# rows can be in any order
while IFS=, read -r field1 field2 || [ -n "$field1" ]
do
    case "$field1" in
        "WEATHER_STATION")
            # Replaces weather station with correctly formatted weather station
            WEATHER_STATION=$field2
            WEATHER_STATION_LIST=$(gridlabd weather index $WEATHER_STATION)
            # Calling it twice. Storing it does not allow line counting. 
            WEATHER_STATION_INDEX_NUMBER=$(gridlabd weather index $WEATHER_STATION | wc -l)
            ;;
        "MODEL")
            MODEL_NAME_INPUT=$field2
            ;;
        "OUTPUT")
            OUTPUT_NAME_INPUT=$field2
            ;;
    esac
done < config.csv

# Handle based on weather stations returned 
if [ $WEATHER_STATION_INDEX_NUMBER -eq 1 ] ; then
    WEATHER_STATION_PARSED=$(basename $WEATHER_STATION_LIST .tmy3)
    gawk -i inplace -F ',' '{gsub(find,replace,$2); print}' find="$WEATHER_STATION" replace="$WEATHER_STATION_PARSED" OFS="," config.csv
elif [ $WEATHER_STATION_INDEX_NUMBER -gt 1 ] ; then
    echo "ERROR [TARIFF_DESIGN] : Could not find unique weather station. Please specify from list below:\n$WEATHER_STATION_LIST"
    exit 1
else 
    echo "ERROR [TARIFF_DESIGN] : Could not find matching weather stations. Please check capitalization and spelling."
    exit 1
fi


# put -t to get template online
gridlabd $MODEL_NAME_INPUT tariff_design.glm
if [ $OUTPUT_NAME_INPUT != "output.csv" ]; then
  mv output.csv $OUTPUT_NAME_INPUT
fi

mv $OUTPUT_NAME_INPUT $OPENFIDO_OUTPUT


exit 0
