# GridLAB-D Analysis Templates

This repository contains the HiPAS GridLAB-D analysis templates.  Templates are published by organizations, which are specified by country and region.  Published organizations are listed in the `.orgs` file.  Each organization publishes templates by listing them in the organization's `.index` file.  Templates are contained in folders, the contents of which are published in `.catalog` files.

# Example

The ICA template published by SLAC is listed in the `US/CA/SLAC` folder.  The template is listed in the `.index` file, and will be included in any index requests.  The folder `ica_analysis` contains the template files. The files listed in the `.catalog` file will be downloaded when the user gets the template.

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

# Publishing Templates

Each organization must be listed in the `.orgs` file to be scanned by the `template` subcommand, e.g., `US/CA/SLAC` is listed. There is no provision for a hierarchy.

Each template must be listed in the organization's `.index` file.

Each file in a template must be listed in the template's `.catalog` file. The format is

~~~
<FILE1>:a=<PERMISSIONS>
<FILE2>:a=<PERMISSIONS>
...
<FILEn>:a=<PERMISSIONS>
~~~

where `<PERMISSIONS>` can be any combination of 'r' and 'x'.

