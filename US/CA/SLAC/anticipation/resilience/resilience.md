Gridlab-D resilience template 

**Currently does not implement impact metric**

The goal of the resilience template:
- Add currently implemented [resilience metrics](https://docs.gridlabd.us/_page.html?&doc=/Module/Resilience/Metrics.md) to model file run with template glm

How to run
- Download any necessary libraries 
- Run `gridlabd <model_file>.glm resilience.glm`

To do 
- Verification: test template works with larger network models
- Validation: compare cost.cpp code with hand calculations
- Add functionality for impact metric using Python on create event handler to avoid segmentation error