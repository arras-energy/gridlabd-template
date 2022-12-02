GridLAB-D templates are used with arbitrary network models.  To run a template with a model use the following commands. 

~~~
bash$ gridlabd template get TEMPLATE
bash$ gridlabd MODELNAME.glm [...] -t TEMPLATE
~~~

where `TEMPLATE` is the template name, and `MODELNAME` is the name of the GLM model file.

Other files can be added to the command line to include model elements such as the clock, recorders, etc.