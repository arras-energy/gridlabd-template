# ICA Analysis

## Background
In California, Investor Owned Utilities (IOUs) are required to complete system-wide integration capacity analysis (ICA) to determine the maximum node level hosting capacity for a circuit to remain within key power system criteria. System ICA results are used to expedite interconnection permitting for distributed energy resource (DER) additions under the Rule 21 interconnection process (Interconnection Use Case). Results must be updated monthly and data must be mapped for review, with hourly capacity limitation data available for download by users. ICA with DER growth scenarios are also required for all annual IOU distribution system planning processes (Planning Use Case). The CPUC provided guidance to IOUs in late 2017 to complete ICA system wide in response to completed IOU demonstration projects and the DER WG final report.

## Overview
The goal of ICA is to quantify the potential DER generation which can interconnect without violating distribution system constraints. This is done through system-wide iterative power flow modeling. DER generation level is varied at each node, independently, until a system violation occurs somewhere within a feeder. The ICA value for that node is then the minimum power injection associated with any violation criteria.

This set of ICA files can be combined with an iterative methodology to check for system constraint violations. At each iteration, the script checks all lines, transformers, regulators, and meters for constraint violations. If one occurs, it records the details of the violation.

## File Structure
The 4 files needed to run an ICA analysis are summarized as follows:

|       Files      |           Location          |                                             Contents                                            |
| ---------------- | --------------------------- | ----------------------------------------------------------------------------------------------- |
| ica-analysis.py  | slacgismo/gridlabd-template | Applies ICA process to network model, checking for constraint violations at every time step     |
| ica-analysis.glm | slacgismo/gridlabd-template | Modifies network model import ica_analysis.py and ica_analysis.csv                              |
| ica-config.csv   | slacgismo/gridlabd-models   | Contains default values for setting violation threshold on network objects. Modifiable by user  |
| model.glm        | slacgismo/gridlabd-models   | Generic network model                                                                           |

The analysis should be run from slacgismo/gridlabd-models using the following command:
```
host% gridlabd template get ica-analysis
host% gridlabd ica-analysis.glm model.glm
```
### ica-analysis.py
This script runs an ICA analysis on the given network model. It sets minimum and maximum thresholds for all the objects and their tracked properties. It then checks the real-time values of those properties on each iteration of the power flow, recording any violations in a dataframe that is written to a csv upon termination of the simulation. A description of each of its functions is included below. 

#### check_phases

Accounts for the phases and configuration aod a meter to determine the voltage properties that should be checked for a given meter.
```
Args: meter

Returns: list of commit properties to check for that meter
```

#### get_commit_val
Accounts for complex number formats and variations in string formatting to return a standardized float value for a given commit property and object
```
Args: object, object class, commit property

Returns: real-time value (float) for of the commit property for the object
```

#### on_init
Sets thresholds for all tracked properties for all tracked objects included in ica-config.csv. Creates a dataframe with properties to check on each commit and their associated thresholds. Sets thresholds by retrieving the library value of each property, and adjusting it according to user inputs in ica-config.csv. For example, if the library value is 1000A, and the user input a 90% threshold, the max threshold would be set to 900A. A table of the tracked classes, the properties that are used to set thresholds (Init Properties), and the properties that are compared against the thresholds (Commit Properties) is included below.
```
Args: timestep

Returns: True
```

|       Class      |       Init Property         | Commit Property              |
| ---------------- | --------------------------- |------------------------------|
| underground_line | rating.summer.continuous    | current_out_A                |
|                  |                             | current_out_B                |
|                  |                             | current_out_C                |
|                  |                             | current_in_A                 |
|                  |                             | current_in_B                 |
|                  |                             | current_in_C                 |
|                  | rating.winter.continuous    | current_out_A                |
|                  |                             | current_out_B                |
|                  |                             | current_out_C                |
|                  |                             | current_in_A                 |
|                  |                             | current_in_B                 |
|                  |                             | current_in_C                 |
|   overhead_line  | rating.summer.continuous    | current_out_A                |
|                  |                             | current_out_B                |
|                  |                             | current_out_C                |
|                  |                             | current_in_A                 |
|                  |                             | current_in_B                 |
|                  |                             | current_in_C                 |
|                  | rating.winter.continuous    | current_out_A                |
|                  |                             | current_out_B                |
|                  |                             | current_out_C                |
|                  |                             | current_in_A                 |
|                  |                             | current_in_B                 |
|                  |                             | current_in_C                 |
|    transformer   | power_rating                | power_in                     |
|                  |                             | power_out                    |
|                  | powerA_rating               | power_in_A                   |
|                  |                             | power_out_A                  |
|                  | powerB_rating               | power_in_B                   |
|                  |                             | power_out_B                  |
|                  | powerC_rating               | power_in_C                   |
|                  |                             | power_out_C                  |
|                  | rated_top_oil_rise          | top_oil_hot_spot_temperature |
|                  | rated_winding_hot_spot_rise | winding_hot_spot_temperature |
|     regulator    | raise_taps                  | tap_A                        |
|                  |                             | tap_B                        |
|                  |                             | tap_C                        |
|                  | lower_taps                  | tap_A                        |
|                  |                             | tap_B                        |
|                  |                             | tap_C                        |
|                  | continuous_rating           | current_out_A                |
|                  |                             | current_out_B                |
|                  |                             | current_out_C                |
|                  |                             | current_in_A                 |
|                  |                             | current_in_B                 |
|                  |                             | current_in_C                 |
|   triplex_meter  | 2* nominal_voltage          | measured_voltage_12          |
|                  | nominal_voltage             | measured_voltage_1           |
|                  |                             | measured_voltage_2           |
|       meter      |       nominal_voltage       | measured_voltage_A           |
|                  |                             | measured_voltage_B           |
|                  |                             | measured_voltage_C           |
|                  |                             | measured_voltage_AB          |
|                  |                             | measured_voltage_BC          |
|                  |                             | measured_voltage_CA          |

#### on_commit
Checks real-time values for all tracked properties for all tracked objects included in ica-config.csv. If the min or max threshold is exceeded, it records the object, violated property, value of property, and time of violation in the violation dataframe.
```
Args: timestep

Returns: True
```

#### on_term
Writes the violation dataframe to a csv. The structure of the csv is determined by the user in ica-config.csv.
```
Args: timestep

Returns: True
```

### ica-analysis.glm
Modifies the network model to read in the ica-config.csv and to run the ica-analysis.py script. 

### ica-config.csv
Includes the default thresholds for all tracked objects and properties in ICA. User can overwrite default values. Properties that are left blank have their thresholds set to their library value. Properties for which the user inputs an X are ignored, and not tracked during ICA. Properties for which the user inputs a percentage have their thresholds set either as a percent deviation from their library value (ex. +- 5%) or as a maximum rating (ex. up to 90% of their library value), in accordance with the table below. Properties for which the user inputs a fixed number have their thresholds set to that number. 

|       Class      |        Init Property        | Interpretation of %     |
| ---------------- | --------------------------- |-------------------------|
| underground_line | rating.summer.continuous    | Rating                  |
|                  | rating.winter.continuous    | Rating                  |
| overhead_line    | rating.summer.continuous    | Rating                  |
|                  | rating.winter.continuous    | Rating                  |
| transformer      | power_rating                | Rating                  |
|                  | powerA_rating               | Rating                  |
|                  | powerB_rating               | Rating                  |
|                  | powerC_rating               | Rating                  |
|                  | rated_top_oil_rise          | Rating                  |
|                  | rated_winding_hot_spot_rise | Rating                  |
| regulator        | raise_taps                  | Error - can not enter % |
|                  | lower_taps                  | Error - can not enter % |
|                  | continuous_rating           | Rating                  |
| triplex_meter    | 2* nominal_voltage          | Deviation               |
|                  | nominal_voltage             | Deviation               |
| meter            | nominal_voltage             | Deviation               |

## Next Directions
