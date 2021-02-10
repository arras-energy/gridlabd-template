ICA Analysis - Integration Capacity Analysis GridLAB-D Template

# Synopsis

~~~
sh% gridlabd MODEL.glm TEMPLATE_PATH/ica_analysis.glm
~~~

# Description

In California, Investor Owned Utilities (IOUs) are required to complete system-wide integration capacity analysis (ICA) to determine the maximum node level hosting capacity for a circuit to remain within key power system criteria. System ICA results are used to expedite interconnection permitting for distributed energy resource (DER) additions under the Rule 21 interconnection process (Interconnection Use Case). Results must be updated monthly and data must be mapped for review, with hourly capacity limitation data available for download by users. ICA with DER growth scenarios are also required for all annual IOU distribution system planning processes (Planning Use Case). The CPUC provided guidance to IOUs in late 2017 to complete ICA system wide in response to completed IOU demonstration projects and the DER WG final report.

The goal of ICA is to quantify the potential DER generation that can interconnect without violating distribution system constraints. This is done through system-wide iterative power flow modeling. DER generation level is varied at each node, independently, until a system violation occurs somewhere within a feeder. The ICA value for that node is then the minimum power injection associated with any violation criteria.

This set of ICA files can be combined with an iterative methodology to check for system constraint violations. At each iteration, the script checks all lines, transformers, regulators, and meters for constraint violations. If one occurs, it records the details of the violation.

## Template Files

Two files needed to run an ICA analysis on a GridLAB-D model are summarized as follows:

| Name | Source | Description |
| :--- | :----- | :---------- |
| ica-analysis.py  | slacgismo/gridlabd-template | Implemenets the ICA process on the model 
| ica-analysis.glm | slacgismo/gridlabd-template | Links the model to the ICA analysis module

Two optional files may also be used to modify how the ICA analysis is performed:

| Name | Location | Description |
| :--- | :------- | :-----------|
| ica_config.csv | $PWD | Table of globals to define after loading the GLM model
| ica_config.glm | $PWD | GLM file to load before loading the GLM model

The analysis should be run from `slacgismo/gridlabd-models using` the following command:
```
host% gridlabd template get ica-analysis
host% export GLD_TEMPLATES="$(gridlabd --version=install)/share/gridlabd/template"
host% gridlabd model.glm $GLD_TEMPLATES/ica_analysis.glm
```

### ica-analysis.glm

This GLM file provides the links between the ICA module and the model that is analyzed.

### ica-analysis.py

This Python module provides the ICA module for GridLAB-D.

### ica-config.csv

Includes information to set default thresholds for all tracked objects and properties in ICA. User can overwrite default values. Properties that are left blank have their thresholds set to their library value. Properties for which the user inputs an X are ignored, and not tracked during ICA. Properties for which the user inputs a percentage have their thresholds set either as a percent deviation from their library value (ex. +- 5%) or as a maximum rating (ex. up to 90% of their library value), in accordance with the table below. Properties for which the user inputs a fixed number have their thresholds set to that number. 

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
| regulator        | raise_taps                  | Error - cannot enter %  |
|                  | lower_taps                  | Error - cannot enter %  |
|                  | continuous_rating           | Rating                  |
| triplex_meter    | 2* nominal_voltage          | Deviation               |
|                  | nominal_voltage             | Deviation               |
| meter            | nominal_voltage             | Deviation               |

`ica-config.csv` also includes 2 user options: (1) `input_option`, and (2) `violation_option`:

1. `input_option`: Can be set to 1 or 2. If 1, `ica-config.csv` is automatically read in through a csv converter. If 2, `ica-config.csv` is read in directly through the python script, allowing for greater flexibility in the format of the csv file.

2. `violation_option`: Can be set to 1, 2, or 3. If 1, the script records the first violation of each object within the violation dataframe. The entire dataframe, with all objects (violated or not) is saved to a csv. If 2, the script records the first violation of each object in a *new* dataframe. This dataframe is saved to a csv, and only includes objects that incurred violations. If 3, the script behaves the same as 2, except *all* violations are recorded, rather than just the first.

### ica-config.glm

This file can contain GLM declarations to modify the model in order to make the ICA module work problem, if needed.
