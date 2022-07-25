#!/bin/bash

for nhouses in 1 2 3
#for ((nhouses = 1.0; nhouses <=2; nhouses = nhouses*2))
do 
    for floorarea in 1000 1500 2000 2500
    do 
        sed -i'' "s/^\(NHOUSES\),.*/\1,$nhouses/" config_template.csv
        sed -i'' "s/^\(FLOORAREA\),.*/\1,$floorarea/" config_template.csv
        echo $nhouses $floorarea
    done
done

#gridlabd model.glm