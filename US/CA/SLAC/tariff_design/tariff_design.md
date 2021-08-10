Tariff Design GridLAB-D Template

# Synopsis

Template for HiPAS tariff design use case. The goal of the use case is to help optimize tariff design by calculating tariffs whiel simulating different energy scenarios. The template calculates TOU tariffs using tariff rate information from the [OpenEI database](https://openei.org/wiki/Utility_Rate_Database) that is developed and maintained by NREL. Simulation is done with HiPAS GridLAB-D. 

Currently the tariff billing calculations are designed for residential TOU tariffs and the OpenEI database tariff formatting. The billing fnc can currently handle TOU tariffs with peak, offpeak, and shoulder (>= 3 rates per day). It calculates the tariff bill hourly.

# Current Issues

Many residential tariffs that are shown on the online OpenEi database many not be available in the csv from the database used to calculate billing.

Bills only have per kWh charges. Additional rates like demand charges, meter charges, DER credits, etc are not included.

# Description

# Template Files

1. tariff_library_config.csv

   User inputs utility name, sector, tariff name, tariff type, tariff region for OpenEI database.

2. config.csv

   User inputs start time, end time, timezone to set simulation parameters.

3. tariff_design.py

   Main py file. Contains fncs to query OpenEI database, fill tariff obj properties, calculate billing hourly.

4. default_billing.py

   Empty py file with empty compute_bill() fnc. Fnc required to use revenue module and billing class.

5. tariff_design.glm

   Gridlabd file defining tariff obj. Defines new properties from OpenEI database for tariff obj.

6. model.glm

   Gridlabd file defining default modules and objs for testing tariff_design.py fncs. 

7. config.glm

   Gridlabd file defining simulation parameters as set in config.csv. 

9. Unused/backup/used for simulation but not directly needed

   gridlabd.json, tariff_design_config.csv tariff_design_config.glm, tariff_library_config.csv, python_backup.py, backup.glm, WA-Yakima_Air_Terminal.glm, CA-San_Francisco_Intl_AP.glm


