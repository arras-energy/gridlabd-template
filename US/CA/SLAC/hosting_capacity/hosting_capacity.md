Hosting Capacity - Template to enable hosting capacity analysis

Synopsis
--------

    sh$ gridlabd MODELNAME.glm -D DER_VALUE='POWER [UNIT]' [-D OPTION=VALUE] -t hosting_capacity

Description
-----------

    Applies a DER load factor to objects of class in DER_CLASS.  Stores analysis
    result in DER_RESULTS.

Options
-------

    DER_VALUE - the multiplier to apply to the property (required)

    DER_CLASS - the object class to modify (default is 'load,triplex_load')

    DER_PROPERTIES - List of properties to save in results (default is '')

    DER_RESULTS - the file to record results in (default is MODELNAME.csv)
