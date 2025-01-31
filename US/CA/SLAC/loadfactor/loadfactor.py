""" Load Factor Template - Template to change the magnitude of loads

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

    LOAD_FACTOR_CLASS - the object class to modify (default is 'load,triplex_load')

    LOAD_FACTOR_PROPERTY - the property to modify (default is 'constant_power_')

    LOAD_FACTOR_LOGFILE - the log file to record changes in (default is None)
"""
try:
    import gldcore
except:
    import gridlabd as gldcore

def on_init(t):
    try:
        # get class of object to modify
        OBJECT_CLASS = gldcore.get_global("LOAD_FACTOR_CLASS")
        if not OBJECT_CLASS:
            OBJECT_CLASS = ["load","triplex_load"]
        if "," in OBJECT_CLASS:
            OBJECT_CLASS = OBJECT_CLASS.split(",")
        elif type(OBJECT_CLASS) is str:
            OBJECT_CLASS = [OBJECT_CLASS]

        # get property to modify
        OBJECT_PROPERTY = gldcore.get_global("LOAD_FACTOR_PROPERTY")
        if not OBJECT_PROPERTY:
            OBJECT_PROPERTY = "constant_power_"

        # get file to load changes
        LOG_FILE = gldcore.get_global("LOAD_FACTOR_LOGFILE")
        if LOG_FILE:
            LOG = open(LOG_FILE,"w")
            print("class,name,property,nominal.real,nominal.reactive,actual.real,actual.reactive",file=LOG)
        else:
            LOG = None

        # get load factor to apply
        LOAD_FACTOR = float(gldcore.get_global("LOAD_FACTOR"))
        if LOAD_FACTOR:
            objects = gldcore.get("objects")
            for obj in objects:
                data = gldcore.get_object(obj)
                if data["class"] in OBJECT_CLASS:
                    for name,value in data.items():
                        if name.startswith(OBJECT_PROPERTY):
                            units = value.split()[1]
                            value = complex(value.split()[0])
                            if abs(value) > 0:
                                modify = value*LOAD_FACTOR
                                if value.imag == 0:
                                    update = str(modify.real)
                                else:
                                    update = f"{str(complex(modify))[1:-1]}"
                                gldcore.set_value(obj,name,update)
                                if LOG:
                                    print(f"{data['class']},{obj},{name},{value.real},{value.imag},{modify.real},{modify.imag}",file=LOG)
    except Exception as err:
        gldcore.warning(f"{obj}.{name}: {err}")
    return True

