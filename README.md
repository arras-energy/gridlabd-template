[![master](https://github.com/slacgismo/gridlabd-template/actions/workflows/master.yml/badge.svg)](https://github.com/slacgismo/gridlabd-template/actions/workflows/master.yml)
[![develop](https://github.com/slacgismo/gridlabd-template/actions/workflows/develop.yml/badge.svg)](https://github.com/slacgismo/gridlabd-template/actions/workflows/develop.yml)

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

