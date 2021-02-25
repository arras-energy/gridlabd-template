ICA Analysis - Integration Capacity Analysis GridLAB-D Template

# Synopsis

~~~
sh% gridlabd -D OUTPUT=<folder> <settings>.glm <network>.glm <recorders>.glm <template-dir>/ica_analysis.glm
~~~

# Description

In California, Investor Owned Utilities (IOUs) are required to complete system-wide integration capacity analysis (ICA) to determine the maximum node level hosting capacity for a circuit to remain within key power system criteria. System ICA results are used to expedite interconnection permitting for distributed energy resource (DER) additions under the Rule 21 interconnection process (Interconnection Use Case). Results must be updated monthly and data must be mapped for review, with hourly capacity limitation data available for download by users. ICA with DER growth scenarios are also required for all annual IOU distribution system planning processes (Planning Use Case). The CPUC provided guidance to IOUs in late 2017 to complete ICA system wide in response to completed IOU demonstration projects and the DER WG final report.

The goal of ICA is to quantify the potential DER generation that can interconnect without violating distribution system constraints. This is done through system-wide iterative power flow modeling. DER generation level is varied at each node, independently, until a system violation occurs somewhere within a feeder. The ICA value for that node is then the minimum power injection associated with any violation criteria.

This set of ICA files can be combined with an iterative methodology to check for system constraint violations. At each iteration, the script checks all lines, transformers, regulators, and meters for constraint violations. If one occurs, it records the details of the violation.

## Template Files

Two files needed to run an ICA analysis on a GridLAB-D model are summarized as follows:

| Name | Source | Description |
| :--- | :----- | :---------- |
| ica-analysis.py  | slacgismo/gridlabd-template | Implements the ICA process on the model 
| ica-analysis.glm | slacgismo/gridlabd-template | Links the model to the ICA analysis module

An optional file `ica_config.csv` may also be used to modify how the ICA analysis is performed.  The parameters that can be set include the following

| Name | Default | Type | Description |
| :--- | :------ | :--- | :-----------|
| `output_folder` | `"."` | `str` | Folder in which output files are stored
| `object_list` | `[]` | `list` | List of load of object names to consider ([] means search for all of class "load")
| `target_properties` | `{"load":"constant_power_{phases}$"}` | `dict` | Target properties to consider in object list
| `delta` | `10000.0` | `float` | Power delta to apply when exploring limits (W)
| `reactive_ratio` | `0.1` | `float`  | Reactive power ratio to use when considering property with zero basis
| `power_limit` | `-1.0e6` | `float` | Minimum power to attempt (W)
| `results_filename` | "solar_capacity.csv" | `str` | File name to use when storing result of analysis

# Example

This example performs a basic ICA in the IEEE-13 bus network model using the following files:

IEEE-13.glm: (see slacgismo/gridlabd-models)

config.csv:

~~~
TEMPLATE,ica_analysis
GLMCONFIG,config.glm
GLMRECORD,
GLMTIMEZONE,PST+8PDT
GLMSTARTTIME,2020-01-01 00:00:00 PST
GLMSTOPTIME,2021-01-01 00:00:00 PST
~~~

config.glm:

~~~
clock 
{
	timezone "PST+8PDT";
	starttime "2020-01-01 00:00:00 PST";
	stoptime "2021-01-01 00:00:00 PST";
}
~~~

The following command runs the analysis

~~~
sh% gridlabd -D OUTPUT=. config.glm IEEE-13.glm $(gridlabd --version=install)/shared/gridlabd/template/ica_analysis/ica_analysis.glm
~~~

The output is as follows:

solar_capacity.csv:
~~~
load,solar_capacity[kW]
Load634,180.0
Load645,0.0
Load646,0.0
Load652,1000.0
Load671,2610.0
Load675,1680.0
Load692,3000.0
Load611,330.0
Load6711,0.0
Load6321,0.0
~~~