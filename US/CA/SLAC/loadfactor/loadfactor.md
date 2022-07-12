Load factor template - Template to change the magnitude of loads

Synopsis
--------

    sh$ gridlabd MODELNAME.glm -D LOAD_FACTOR=SCALAR [-D OPTION=VALUE] -t loadfactor

Description
-----------

    Applies a load factor to object of class in LOAD_FACTOR_CLASS with property
    names starting with LOAD_FACTOR_PROPERTY.  Logs updates in LOAD_FACTOR_LOGFILE.

Options
-------

    LOAD_FACTOR - the multiplier to apply to the property (required)

    LOAD_FACTOR_CLASS - the object class to modify (default is 'load')

    LOAD_FACTOR_PROPERTY - the property to modify (default is 'constant_power_')

    LOAD_FACTOR_LOGFILE - the log file to record changes in (default is None)
