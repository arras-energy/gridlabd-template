[![master](https://github.com/arras-energy/gridlabd-template/actions/workflows/master.yml/badge.svg)](https://github.com/arras-energy/gridlabd-template/actions/workflows/master.yml)
[![develop](https://github.com/arras-energy/gridlabd-template/actions/workflows/develop.yml/badge.svg)](https://github.com/arras-energy/gridlabd-template/actions/workflows/develop.yml)

To view the online documentation please use the [Docs Browser](https://docs.gridlabd.us/) and select the `gridlabd-template` project.
# GridLAB-D Analysis Templates

This repository contains the HiPAS GridLAB-D analysis templates.  To use a template in GridLAB-D you must first download the template from the template repository. To see the list of available templates, use the `template index` subcommand, e.g.,

~~~
% gridlabd template index
ica_analysis
~~~

To download a template, use the `template get` subcommand, e.g.,

~~~
% gridlabd template get ica_analysis
~~~

To use a template, simply include it on the gridlabd command line using the `-t|--template` option after the model you want it to be applied to, e.g.,

~~~
% gridlabd my_model.glm --template ica_analysis
~~~

You can embed a template in a GLM model using the following macros:

~~~
#template get ica_analysis
#option template ica_analysis
~~~

# Publishing Templates

Templates are published by organizations, which are specified by country and region.  Published organizations are listed in the `.orgs` file.  Each organization publishes templates by listing them in the organization's `.index` file.  Templates are contained in folders, the contents of which are published in `.catalog` files.

# Template Repository Structure

Each organization must be listed in the `.orgs` file to be scanned by the `template` subcommand, e.g., `US/CA/SLAC` is listed. There is no provision for a hierarchy. 

Each template must be listed in the organization's `.index` file. 

The files listed in the `.catalog` file will be downloaded when the user gets the template.

~~~
+- .orgs
+- <COUNTRY1>/
|  +- <REGION1>/
|  |  +- <ORG1>/
|  |  |  +- .index
|  |  |  +- <TEMPLATE1>/
|  |  |  |  +- .catalog
|  |  |  |  +- <FILE1>
|  |  |  |  +- <FILE2>
|  |  |  |  +- ...
|  |  |  |  +- <FILEn>
|  |  |  |- <TEMPLATE2>/
|  |  |  |- ...
|  |  |  |- <TEMPLATEn>/
|  |  +- <ORG2>/
|  |  +- ...
|  |  +- <ORGn>/
|  +- <REGION2>/
|  +- ...
|  +- <REGIONn>/
+- <COUNTRY2>/
+- ...
+- <COUNTRYn>/
~~~

# Template Catalogs

Each file in a template must be listed in the template's `.catalog` file. The catalog format is

~~~
<FILE1>:a=<PERMISSIONS>
<FILE2>:a=<PERMISSIONS>
...
<FILEn>:a=<PERMISSIONS>
~~~

where `<PERMISSIONS>` can be any combination of 'r' and 'x'.

# Validation

This repository automatic validates the templates with models in the `autotest/models` submodule. To get the latest version of the test models, use the `make models` commands.  This will require a new pull request to update and validate the repository if the models are changed.

Each template must have an `autotest` folder to have validation performed. Within the autotest folders, the `autotest/models` folder structure must be replicated, except that for each `glm` in the models tree a folder by the same name must be created and a file name `autotest.glm` must be created within it.  You may use the `./create_autotest TEMPLATE` to perform this task on a template.  The `autotest.glm` should contain any GLM model elements, macros, etc. necessary to run the run the validation test.

## Running Validation

To run the validate test, use the `make validate` command.  The test command is 

~~~
gridlabd -D pythonpath=TEMPLATEDIR -W OUTPUTDIR autotest.glm MODELNAME.glm -o gridlabd.json TEMPLATE.glm 1>OUTPUTDIR/gridlabd.out" 2>&1
~~~

If the validation test fails then the test result is reported as `FAIL`.

Results are written to the `test` folder in a tree that replicates the template source tree.  Output files are written to the `OUTPUTDIR` folders created by the `create_autotest` command. These output files will be compared to reference copies in the template `autotest` folder. If the files are different then the test result is reported as `DIFFER`. At this time only CSV files are compared.

## Validation Test Results

If the validation test succeeds and the files match then the test result is reported as `OK.`

The contents of the `test` folder are delivered in a file called `validate.tar.gz`, which is made available for download when the validation workflow fails.

## Validation Test Data

To update the validate test data use by a template, run the command `./update_results.sh TEMPLATE`. This will copy the test results back to the template `autotest` folder to use as reference data for future validation tests.

A validate data report is created using the `make report` command. The report documents the `autotest` data used to compare the results of validation tests. The report can be downloaded from https://github.com/slacgismo/gridlabd-template/raw/develop/report/Validation_Report.pdf.
