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
#### check_phases

Accounts for the phases and configuration aod a meter to determine the voltage properties that should be checked for a given meter.

Args: meter

Returns: list of commit properties to check for that meter

#### get_commit_val
Accounts for complex number formats and variations in string formatting to return a standardized float value for a given commit property and object

Args: object, object class, commit property

Returns: real-time value (float) for of the commit property for the object

#### on_init
Sets thresholds for all tracked properties for all tracked objects included in ica-config.csv. Creates a dataframe with properties to check on each commit and their associated thresholds. Sets thresholds by retrieving the library value of each property, and adjusting it according to user inputs in ica-config.csv. For example, if the library value is 1000A, and the user input a 90% threshold, the max threshold would be set to 900A. 

Args: timestep

Returns: True

#### on_commit
Checks real-time values for all tracked properties for all tracked objects included in ica-config.csv. If the min or max threshold is exceeded, it records the object, violated property, value of property, and time of violation. Writes the violation log to a csv. The contents of the csv is determined by the user in ica-config.csv.

Args: timestep

Returns: True

### ica-analysis.glm
Modifies the network model to read in the ica-config.csv and to run the ica-analysis.py script. 

### ica-config.csv
Populated with default thresholds for all tracked objects and properties in ICA. User can overwrite default values. 

## Next Directions
