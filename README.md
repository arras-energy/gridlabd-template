# GridLAB-D Analysis Templates

This repository contains the HiPAS GridLAB-D analysis templates.  Templates are published by organizations, which are specified by country and region.  Published organizations are listed in the `.orgs` file.  Each organization publishes templates by listing them in the organization's `.index` file.  Templates are contained in folders, the contents of which are published in `.zip` folders.

## Example

The organization `US/CA/SLAC` is listed in `.orgs` and publishes the template for integrated capacity analysis in the folder `US/CA/SLAC/ica_analysis`.  The template is compiled in the file `US/CA/SLAC/ica_analysis.zip`, which is listed in the index file `US/CA/SLAC/.index`.

# Publishing Templates

When a change is made to a template or a new template is created, the `publish.sh` script updates the templates from the indexes.

## Example

The following example illustrates how the ICA template was first published

~~~
bash$ ./compile
Creating US/CA/SLAC/ica_analysis.zip...done
~~~

The following exmaple illustrates how the ICA template is updated when a file changes

~~~
bash$ touch US/CA/SLAC/ica_analysis/ica_analysis.glm
bash$ ./compile
Updating US/CA/SLAC/ica_analysis.zip...done
~~~

Note that after the `compile` script is run, you must push that changes to the main repository.  Please observe the usual convention for creating pull requests, as pushing directly to `master` is not permitted.
