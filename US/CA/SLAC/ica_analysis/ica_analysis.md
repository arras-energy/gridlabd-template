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
| ica-analysis.glm | slacgismo/gridlabd-template | Modifies network model by importing ica_analysis.py and ica_analysis.csv                        |
| config.csv       |                             | Containers user-specified values to test network objects. Default is used if not provided       |
| model.glm        | slacgismo/gridlabd-models   | Generic network model                                                                           |

The analysis is currently run from the docker image `slacgismo/gridlabd:develop` with the following command:
```
docker run -itv "<path_to_template>":/model slacgismo/gridlabd:develop
```
### ica-analysis.py
This script runs an ICA analysis on the given network model. It sets minimum and maximum thresholds for all the objects and their tracked properties. It then checks the real-time values of those properties on each iteration of the power flow simulation, recording any violations in a dataframe that is written to a csv upon termination of the simulation. A description of each of its functions is included below. 

#### def on_init(t):
Processes each object in the model and sets up default violation values using config.csv. 


### ica-analysis.glm
Reads in  `config.csv` and runs the `ica-analysis.py` script. 

### config.csv
Optional. User provided csv file to specify default values globals `VOLTAGE_VIOLATION_THRESHOLD` and `VOLTAGE_FLUCTUATION_THRESHOLD`, along with `DER_VALUE` of the list of loads `LOAD_LIST`, and `VIOLATION_RATING` of links. Example config.csv is provided below:

```
DER_VALUE,-10000
LOAD_LIST, R1-12_47-1_load_4 R1-12_47-1_load_11 R1-12_47-1_load_15 
VOLTAGE_VIOLATION_THRESHOLD, 0.03
VOLTAGE_FLUCTUATION_THRESHOLD, 0.05
VIOLATION_RATING, 0.03
```


## Next Directions

1. Generalize - test ICA methodology on other IEEE networks (IEEE4, IEEE13, IEEE57, IEEE8500) 
2. Validate - confirm that this ICA methodology produces similar results to CYME. Conduct sensitivity analyses.
3. Enhance - work with utilities to identify ways in which ICA methodology could be improved upon. Ex) applying ML to replace iterative methodology
