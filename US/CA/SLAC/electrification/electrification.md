#Electrification Analysis GridLAB-D Template

## Configuration 

To configure the model use file `config.csv`. For example:

| WEATHER | CA-San_Jose_Intl_Ap.tmy3
| NHOUSES_ELEC | 20
| NHOUSES_GAS | 10
| TIMEZONE | PST+8PDT
| YEAR | 2020
| HEATINGSYSTEMTYPE | HEAT_PUMP
| COOLINGSYSTEMTYPE | HEAT_PUMP
| HEATINGSETPOINT | 71
| COOLINGSETPOINT | 74
| THERMALINTEGRITYLEVEL | GOOD
| GASENDUSES | HOTWATER
| CURRDUMP | ENABLE

Appliances that can defined as `GASENDUSES`, separate by '|':

| Clothes Dryer | DRYER
| Waterheater | WATERHEATER
| Cooking | RANGE

To specify gas heating, use `HEATINGSYSTEMTYPE,GAS`.

## Running the model 

1. Create your `config.csv`
2. Get the template: `gridlabd template get electrification`
3. Run the template: `gridlabd config.csv -t electrification` 

## Output

The output  will appear in `electrification.csv` and `electrification.png`. The total annual energy use and the peak demand are recorded and plotted.

