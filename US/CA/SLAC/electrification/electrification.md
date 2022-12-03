# Electrification Analysis GridLAB-D Template

The electrification template applies a residential electrification model to the GLM file. The specified number of 100% electric and partial gas house are added to the model and the simulation is run for the year (and optionally only the month) specified. The results are output as a CSV file with the peak load and total energy use on each phase.  A plot of the results is also generated.

## Configuration 

To configure the model use file `config.csv` or `config.glm`. For example:

| Parameter | Example | Default
| WEATHER | CA-San_Jose_Intl_Ap.tmy3 | None
| NHOUSES_ELEC | 20 | 1
| NHOUSES_GAS | 10 | 0
| TIMEZONE | PST+8PDT | PST+8PDT
| YEAR | 2020 | 2020
| MONTH | 7 | None
| HEATINGSYSTEMTYPE | HEAT_PUMP | HEAT_PUMP 
| COOLINGSYSTEMTYPE | HEAT_PUMP | HEAT_PUMP 
| HEATINGSETPOINT | 71 | 70
| COOLINGSETPOINT | 74 | 75
| THERMALINTEGRITYLEVEL | GOOD | GOOD
| GASENDUSES | WATERHEATER | WATERHEATER\|DRYER\|RANGE

Valid `GASENDUSES` are:

| Clothes Dryer | DRYER
| Waterheater | WATERHEATER
| Cooking | RANGE

To specify gas heating, use `HEATINGSYSTEMTYPE` `GAS`. To disable air conditioning use `COOLINGSYSTEMTYPE` `NONE`.

## Running the model 

1. Create your `config.csv` of `config.glm` file.
2. Get the template: `gridlabd template get electrification`
3. Run the template: `gridlabd CONFIGFILE [MODELFILE] -t electrification` 

## Output

The output  will appear in `electrification.csv` and `electrification.png`. The total annual energy use and the peak demand are recorded and plotted.

