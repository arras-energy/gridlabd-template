""" Hosting Capacity - Template to enable hosting capacity analysis

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
"""
import sys
import gridlabd

def on_init(t):
    try:
        # get class of object to modify
        OBJECT_CLASS = gridlabd.get_global("DER_CLASS")
        if not OBJECT_CLASS:
            OBJECT_CLASS = ["load","triplex_load"]
        if "," in OBJECT_CLASS:
            OBJECT_CLASS = OBJECT_CLASS.split(",")
        elif type(OBJECT_CLASS) is str:
            OBJECT_CLASS = [OBJECT_CLASS]

        # get properties
        DER_PROPERTIES = gridlabd.get_global("DER_PROPERTIES")
        if not DER_PROPERTIES:
            DER_PROPERTIES = "DER_value,voltage_violation_threshold,undervoltage_violation_threshold,overvoltage_violation_threshold,voltage_fluctuation_threshold,violation_detected"

        # get load factor to apply
        DER_VALUE = gridlabd.get_global("DER_VALUE")
        if DER_VALUE:
            objects = gridlabd.get("objects")
            for obj in objects:
                data = gridlabd.get_object(obj)
                if data["class"] in OBJECT_CLASS:
                    if "DER_value" in data.keys():
                        gridlabd.set_value(obj,name,DER_VALUE)
    except:
        e_type,e_value,e_trace = sys.exc_info()
        e_file = os.path.basename(e_trace.tb_frame.f_code.co_filename)
        e_line = e_trace.tb_lineno
        gridlabd.error(f"{e_type.__name__} ({e_file}:{e_line}): {e_value}")
        return False
    return True

def on_term(t):
    # get file to store result
    DER_RESULTS = gridlabd.get_global("DER_RESULTS")
    if DER_RESULTS:
        RESULTS = open(DER_RESULTS,"w")
        print("class,object,"+DER_PROPERTIES,file=RESULTS)
        objects = gridlabd.get("objects")
        for obj in objects:
            data = gridlabd.get_object(obj)
            if data["class"] in OBJECT_CLASS:
                for prop in DER_PROPERTIES.split(","):
                    if prop in data.keys():
                        print(","+gridlabd.get_value(obj,prop),end='',file=RESULTS)
                    else:
                        raise Exception(f"property '{prop}' not found in object '{obj}'")
            print('',file=RESULTS)
