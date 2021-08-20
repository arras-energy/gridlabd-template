Tariff Design GridLAB-D Template

## This document outlines how to use the HIPAS tariff design use case simulation template

# Synopsis

To run this template, open an instance of GridLAB-D in Docker and run the following command: gridlabd model.glm tariff_design.glm. Ensure that the required files in .catalog are downloaded before running.

# Description

The goal of the use case is to help optimize tariff designs by calculating tariffs and electrical bills given input house and load characteristics. The template calculates TOU tariffs using tariff rate information from the [OpenEI database](https://openei.org/wiki/Utility_Rate_Database) that is developed and maintained by NREL. Simulation is done with HiPAS GridLAB-D. 

Currently the tariff billing calculations are designed for residential TOU tariffs and the OpenEI database tariff formatting. The billing fnc can currently handle TOU tariffs with peak, offpeak, and shoulder (>= 3 rates per day). It calculates the tariff bill hourly.

# Example

1. Ensure the required files are from the .catalog are downloaded 
2. Create or obtain a model.glm file with at least a default house and triplex meter object, start and stop time, a tmy climate file defined
3. Open a GridLAB-D docker container and run gridlabd model.glm tariff_design.glm
4. Enter the desired row index from the tariff_library_config.csv for the tariff that should be simulated


# Caviates

Many residential tariffs that are shown on the online OpenEi database many not be available in the downloaded csv from the database used to calculate billing.

Bills only have per kWh charges. Additional rates like demand charges, meter charges, DER credits, etc are not included.

The billing function was developed to work with the OpenEI database formatting and is not that intuitive to understand or translate to other tariff databases.

# TO DO

- [ ] Update md documentation with code edits listed in pull request. Especially example documentation.
- [ ] Bug where billing for PG&E E-6 and Electric Vehicle EV-2 and EV-B tariffs are not calculated correctly.
- [ ] Add code to add user defined tariff input, ie not a predefined tariff from the OpenEI database.
- [ ] Add code to config.csv and on_term event handler to write results to user defined csv.





