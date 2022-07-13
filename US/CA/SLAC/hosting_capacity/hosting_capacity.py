""" Hosting Capacity - Template to enable hosting capacity analysis

Synopsis
--------

    sh$ gridlabd MODELNAME.glm -D DER_VALUE='POWER' [-D OPTION=VALUE] -t hosting_capacity

Description
-----------

    Applies a DER load factor to objects of class in DER_CLASS.  Stores analysis
    result in DER_RESULTS.

Options
-------

    DER_VALUE - the multiplier to apply to the property (required)

    DER_CLASS - the object class to modify (default is 'load,triplex_load')

    DER_PROPERTIES - List of properties to save in results (default is 'DER_value,voltage_violation_threshold,undervoltage_violation_threshold,overvoltage_violation_threshold,voltage_fluctuation_threshold,violation_detected')

    DER_RESULTS - the file to record results in (default is hosting_capacity.csv)
"""
import sys, os
import gridlabd

def on_init(t):
    try:
        # get class of object to modify
        global DER_CLASS
        DER_CLASS = gridlabd.get_global("DER_CLASS")
        if not DER_CLASS:
            DER_CLASS = ["load","triplex_load"]
        if "," in OBJECT_CLASS:
            DER_CLASS = DER_CLASS.split(",")
        elif type(OBJECT_CLASS) is str:
            DER_CLASS = [DER_CLASS]

        # get properties
        global DER_PROPERTIES
        DER_PROPERTIES = gridlabd.get_global("DER_PROPERTIES")
        if not DER_PROPERTIES:
            DER_PROPERTIES = "DER_value,voltage_violation_threshold,undervoltage_violation_threshold,overvoltage_violation_threshold,voltage_fluctuation_threshold,violation_detected"

        # get load factor to apply
        DER_VALUE = gridlabd.get_global("DER_VALUE").strip('"').split()
        if DER_VALUE:
            value = str(complex(DER_VALUE[0])).strip("()")
            if len(DER_VALUE) > 1:
                units = DER_VALUE[1]
            else:
                units = ""
            objects = gridlabd.get("objects")
            for obj in objects:
                data = gridlabd.get_object(obj)
                if data["class"] in DER_CLASS:
                    gridlabd.set_value(obj,"DER_value",str(value))
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
    if not DER_RESULTS:
        DER_RESULTS = "hosting_capacity.csv"
    RESULTS = open(DER_RESULTS,"w")

    # save results
    print("class,object,"+DER_PROPERTIES,file=RESULTS)
    objects = gridlabd.get("objects")
    for obj in objects:
        data = gridlabd.get_object(obj)
        if data["class"] in DER_CLASS:
            for prop in DER_PROPERTIES.split(","):
                if prop in data.keys():
                    print(","+gridlabd.get_value(obj,prop),end='',file=RESULTS)
                else:
                    raise Exception(f"property '{prop}' not found in object '{obj}'")
        print('',file=RESULTS)

    close(RESULTS)

