"""Integration Capacity Analysis (ICA) gridlabd-python module

This gridlabd python module implements a fast ICA. It should be used in conjunction
with the gridlabd model file "ica_analysis.glm".  The canonical command line is

    shell% gridlabd config.glm equipment.glm network.glm loads.glm ica_analysis.glm

where the model files contain the following

    config.glm          specifies the timeframe of the analysis using the `clock` directive, 
                        as well as any other needed settings
    equipment.glm       specifies the library devices used in the analysis
    network.glm         specifies the network topology
    loads.glm           specifies the loads
    ica_analysis.glm    links and enables the ICA analysis module

The ICA analysis files may be downloaded from the GridLAB-D template library using the command

    shell% gridlabd template get ica_analysis

"""

import sys, re, csv, datetime
try:
    import gldcore
except:
    import gridlabd as gldcore

# 
# Module globals
#
output_folder = "." # folder in which output files are stored
delta = 10000.0 # power delta to apply when considering properties (W)
reactive_ratio = 0.1 # reactive power ratio to use when considering property with zero basis
power_limit = -1.0e6 # minimum power to attempt (W)
voltage_limit = 0.03 # maximum power devation (pu)
results_filename = "solar_capacity.csv" # file name to use when storing result of analysis
details_filename = "violation_details.csv" # file name in which to write violation details data

object_list = [] # list of load of objects to consider ([] mean search for all of class "load")
target_properties = {"load":{"constant_power_{phases}$":"POWER","measured_voltage_{phases}$":"VOLTAGE"}} # target properties to consider in object list
property_list = {} # properties found to use when considering objects
limit_list = {} # list of limits found in objects considered


# read globals from py config
try:
    from ica_config import *
except ModuleNotFoundError:
    pass
except:
    raise

# read globals from csv config
config_allowed = {
    "output_folder" : 
    {
        "default" : output_folder,
        "description" : "Folder in which the output files are stored",
        "type" : ["str"],
        "validate" : 
        {
            "str": {"path not found": lambda f: sys.path.exists(f)},
        },
    }, 
    "delta" : 
    {
        "default" : delta,
        "description" : "Power delta to apply when considering property (unit of W)",
        "type" : ["float"],
        "validate" : 
        {
            "float": {"value is not positive" : lambda x: x>0},
        },
    },
    "reactive_ratio" : 
    {
        "default" : reactive_ratio,
        "description" : "Reactive power ratio to use when considering property with zero basis",
        "type" : ["float"],
        "validate" : 
        {
            "float" : { "value is not positive" : lambda x: x>0 },
        },
    },
    "power_limit" : 
    {
        "default" : power_limit,
        "description" : "Minimum power to attempt (W)",
        "type" : ["float"],
        "validate" : 
        {
            "float" : { "value is not negative or zero" : lambda x: x<=0 },
        },
    },
    "voltage_limit" : 
    {
        "default" : voltage_limit,
        "description" : "maximum power devation (pu)",
        "type" : ["float"],
        "validate" : 
        {
            "float" : { "value is not positive" : lambda x: x>0 },
        },
    },
    "results_filename" : 
    {
        "default" : results_filename,
        "description" : "File name to use when storing result of analysis",
        "type" : ["str"],
        "validate" : 
        {
        },
    },
    "details_filename" : 
    {
        "default" : details_filename,
        "description" : "File name in which to write violation details data",
        "type" : ["str"],
        "validate" : 
        {
        },
    },
}
try:
    with open("ica_config.csv","r") as fh:
        reader = csv.reader(fh)
        for row in reader:
            name = row[0]
            if not name in config_allowed.keys():
                raise Exception(f"ica_config.csv: '{name}' is not an allowed ica_analysis configuration option")
            value = row[1]
            vtype = type(globals()[name])
            globals()[name] = vtype(value)
except FileNotFoundError:
    pass
except:
    raise

#
# Module utilities
#

def add_property(objname,propname,limittype,nonzero=True,noexception=True,onexception=gldcore.warning):
    """Add a property to the list of properties to consider

    Parameters:
        objname (str): name of object
        propname (str): name of property
        nonzero (bool): flag to restrict addition to properties that have a non-zero base value
        noexception (bool): flag to not raise exception and use `onexception()` instead
        onexception (callable): function to call when noexception is used and add fails
    """
    global property_list
    
    try:
        # get the property
        prop = gldcore.property(objname,propname)

        # get the value of the property
        value = prop.get_value()

        # if the value should be added
        if not nonzero or value != 0.0:

            # if the object is not already listed
            if not objname in property_list.keys():

                # create a new entry for the value in the property list
                property_list[objname]={propname:[prop,value,limittype]}

                # create a new entry for the result in the limit list
                limit_list[objname] = {}

            # the object is already list
            else:

                # add the property to the object's property list
                property_list[objname][propname] = [prop,value,limittype]
    except:

        # if no exceptions are allowed
        if noexception:

            # call the output function
            onexception(f"unable to add to {objname}.{propname}")

            # continue without further ado
            pass
        else:

            # raise the exception
            raise

#
# GridLAB-D event handlers
#
def on_init(t):
    """GridLAB-D initialization event handler

    Parameter:
        t (int): initial timestamp

    Return:
        bool: success (True) or failure (False)
    """
    global output_folder
    global object_list
    global target_properties

    # get the output folder name from the global variable list
    output_folder = gldcore.get_global("OUTPUT")

    # if none is defined
    if not output_folder:

        # use the current working direction
        output_folder = "."

    # if objects to consider are not specified
    if not object_list:

        # use list of all objects
        object_list = gldcore.get("objects")

    # for each object in the object list
    for objname in object_list:

        # the object's class
        classname = gldcore.get_value(objname,"class")

        # if the class is listed among the targets
        for classname, target_list in target_properties.items():

            # get the object's data
            objdata = gldcore.get_object(objname)

            # if the object has phase data
            if "phases" in objdata.keys():

                # get the object's class structure
                classdata = gldcore.get_class(classname)

                # for each property in the class's target property list
                for property_name, limittype in target_list.items():

                    # get the property pattern to use, and replace phase information pattern, if any
                    pattern = property_name.replace("{phases}",f"[{objdata['phases']}]")

                    # for each property in the class
                    for propname in classdata.keys():

                        # if the property matches the pattern
                        if re.match(pattern,propname):

                            # add the property to the list of properties to consider
                            add_property(objname,propname,limittype,nonzero=False)

    # successfully initialized
    return True

def on_sync(t):
    """GridLAB-D synchronization event handler

    Parameter:
        t (int): target timestamp

    Return:
        int: timestamp of next desired sync event call
    """
    global property_list
    global limit_list

    # get the current timestamp in human readable form
    dt = gldcore.get_global("clock")
    gldcore.debug(f"*** onsync({dt}) ***")

    # determine whether a violation has occurred
    violation_active = int(gldcore.get_global("powerflow::violation_active"))
    if violation_active:
        gldcore.debug(f"{dt}: violation detected (violation_active={violation_active})")

    # start by assuming there's nothing left to do with the property being considered
    done = None

    # if there's still a property to consider
    if property_list:

        # get the object name of the property to consider (the first one in the list of keys
        objname = list(property_list.keys())[0]
        gldcore.debug(f"{dt}: updating {objname}")
        if objname not in limit_list:
            limit_list[objname] = {}

        # get the properties being considered for this object
        proplist = property_list[objname]

        # if the property list is non-empty
        if proplist:

            # for each property in the object's property list
            for propname, specs in proplist.items():
                if propname not in limit_list[objname]:
                    limit_list[objname][propname] = {}

                # get the property name and the property's original value
                prop = specs[0]
                base = specs[1]
                limit = specs[2]

                # if the original value is zero
                if base.real == 0.0:

                    # consider property by fixed increment specified by delta and reactive_ratio
                    value = prop.get_value() - complex(delta,delta*reactive_ratio)

                # original value is non-zero
                else:

                    # consider property by relative increments specified by delta
                    value = prop.get_value() - base/base.real*delta

                # if a violation has occurred
                if violation_active:
                    gldcore.debug(f"{dt}: resetting {objname}.{propname} to base {base}")

                    # reset the property to its original value
                    prop.set_value(base)

                    # record the load limit
                    if not objname in limit_list.keys() or not propname in limit_list[objname].keys():
                        load_limit = base - value
                        limit_list[objname][propname] = {
                            "timestamp" : dt, 
                            "real" : round(load_limit.real,1), 
                            "reactive" : round(load_limit.imag,1)}
                    limit_list[objname][propname]["violation"] = gldcore.get_value(objname,"violation_detected")

                    # flag that processing is done
                    done = objname

                # if the maximum solar limit is reached
                elif power_limit and value.real < power_limit and limit == "POWER":
                    gldcore.debug(f"{dt}: power limit reach for {objname}.{propname} = {value}")

                    # reset the property to its original value
                    prop.set_value(base)

                    # record the load limit
                    if not objname in limit_list.keys() or not propname in limit_list[objname].keys():
                        load_limit = base - value
                        limit_list[objname][propname] = {
                            "timestamp" : dt, 
                            "real" : round(load_limit.real,1), 
                            "reactive" : round(load_limit.imag,1)}
                    limit_list[objname][propname]["violation"] = "POWERLIMIT"

                    # flag that processing is done
                    done = objname

                # if the maximum solar limit is reached
                elif voltage_limit and base.real != 0.0 and abs((value.real-base.real)/base.real) > voltage_limit and limit == "VOLTAGE":
                    gldcore.debug(f"{dt}: power deviation limit reach for {objname}.{propname} = {value}")

                    # reset the property to its original value
                    prop.set_value(base)

                    # record the load limit
                    if not objname in limit_list.keys() or not propname in limit_list[objname].keys():
                        load_limit = base - value
                        limit_list[objname][propname] = {
                            "timestamp" : dt, 
                            "real" : round(load_limit.real,1), 
                            "reactive" : round(load_limit.imag,1)}
                    limit_list[objname][propname]["violation"] = "VOLTAGELIMIT"

                    # flag that processing is done
                    done = objname


                # if no violation has occurred
                else:
                    gldcore.debug(f"{dt}: updating {objname}.{propname} = {value}")

                    # set the new value of the property
                    prop.set_value(value)

                    # compute the load limit implied by this value
                    load_limit = base - value

                    # record the load limit
                    limit_list[objname][propname] = {
                        "timestamp": dt, 
                        "real": round(load_limit.real,1), 
                        "reactive": round(load_limit.imag,1),
                        "violation" : "NONE"
                        }

        # the property list is empty
        else:

            # flag that processing is done
            done = objname


        # if done
        if done:
            gldcore.debug(f"{dt}: finished with {objname}")

            # if property list is empty
            if proplist == {}:

                # remove the object from the list of properties to consider
                del property_list[objname]

            # the property list is not empty
            else:

                # clear the property list (this will allow an extra solver iteration to clear the violation)
                property_list[objname] = {}

            # if the property list is non-empty
            if property_list:
                gldcore.debug(f"{dt}: next is {list(property_list.keys())[0]}")

        # if a violation occurred
        if violation_active:

            # clear the violation
            gldcore.debug(f"{dt}: clearing violation")
            gldcore.set_global("powerflow::violation_active","0")

        # wait 1 minute for controls to settle before trying the next value
        tt = t+60
        gldcore.debug(f"updating to {datetime.datetime.fromtimestamp(tt)}")
        return tt

    # no objects or properties left to consider
    else:

        # nothing left to do
        gldcore.debug(f"updating to NEVER")
        return gldcore.NEVER

def on_term(t):
    """GridLAB-D on_term event handler

     Parameter:
        t (int): target timestamp   
    """
    global output_folder
    global limit_list

    # open the results file
    with open(f"{output_folder}/{results_filename}","w") as fh:

        # create a CSV writer
        writer = csv.writer(fh)

        # write the header
        writer.writerow(["load","solar_capacity[kW]"])

        # for each item in the limit results
        for objname, property_data in limit_list.items():
            
            # accumulate the total power recorded
            power = None
            for propname, data in property_data.items():
                try:
                    if not power:
                        power = 0.0
                    power += data["real"]/1000.0
                except:
                    gldcore.warning(f"no real power in data={data}")
                    pass

            # write the total power
            writer.writerow([objname,round(power,1) if power != None else None])

    if type(details_filename) is str:
        header = None
        with open(f"{output_folder}/{details_filename}","w") as fh:
            writer = csv.writer(fh)
            for objname, property_data in limit_list.items():
                for propname, data in property_data.items():
                    if not header:
                        header = ["objname","propname"]
                        header.extend(list(data.keys()))
                        writer.writerow(header)
                    rowdata = [objname,propname]
                    rowdata.extend(list(data.values()))
                    writer.writerow(rowdata)

if len(sys.argv) > 1:
    if  sys.argv[1] in  ["-d","--defaults"]:
        for var, spec in config_allowed.items():
            print(f"#\n# {spec['description']}\n#")
            print(f"{var},{spec['default']}\n")
    elif sys.argv[1] in ["-h","--help"]:
        print("Syntax: ica_analysis.py [-h|--help] [-d|--defaults]")
    else:
        raise Exception(f"{sys.argv[1]} is not a valid command argument")
