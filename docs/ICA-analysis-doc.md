# ICA Analysis
## ICA Overview

The goal of ICA is to quantify the potential DER generation which can interconnect without violating distribution system constraints. This is done through system-wide iterative power flow modeling. DER generation level is varied at each node, independently, until a system violation occurs somewhere within a feeder. The ICA value for that node is then the minimum power injection associated with any violation criteria.

The set of ICA files described below can be combined with an iterative methodology to check for system constraint violations. At each iteration, the script checks all lines, transformers, regulators, and meters for constraint violations. If one occurs, it records the details of the violation.

## ICA File Management

The 4 files needed to run an ICA analysis are summarized as follows:

|       Files      |           Location          |                                             Contents                                            |
| ---------------- | --------------------------- | ----------------------------------------------------------------------------------------------- |
| ica-analysis.py  | slacgismo/gridlabd-template | Applies ICA process to network model, checking for constraint violations at every time step     |
| ica-analysis.glm | slacgismo/gridlabd-template | Modifies network model import ica_analysis.py and ica_analysis.csv                              |
| ica-config.csv   | slacgismo/gridlabd-models   | Contains default values for setting violation threshold on network objects. Modifiable by user  |
| model.glm        | slacgismo/gridlabd-models   | Generic network model                                                                           |

The analysis should be run from ??? using the following command:
```
host% gridlabd template get ica-analysis
host% gridlabd ica-analysis.glm model.glm
```
