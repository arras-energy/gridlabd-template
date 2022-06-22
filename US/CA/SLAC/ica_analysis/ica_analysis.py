#!/usr/bin/env python3
import gridlabd 

"""
Created on Tue June 21 2020

Sets up model objects based on user values in config.csv. Config.csv and all its values are optional. 
    
To use this, use the following command line:
    
    host% gridlabd <mymodel>.glm ica_analysis.glm
    
@author: johnsonhsiung
"""

def is_node(data) -> bool:
    # Checks to see if data by checking the existence of property "DER_value". This takes into account objects of a class extending the node class. 
    if data.get("DER_value"):
        return True
    return False
def is_load(data) -> bool:
    # Checks to see if data is a load by comparing the class. 
    if data.get("class") == "load":
        return True
    return False
def is_link(data) -> bool:
    # Checks to see if data is a link by checking the existence of property "from" and "to". This takes into account objects of a class extending the link class. 
    if data.get("from") and data.get("to"):
        return True
    return False
def parse_user_DER(der_value) -> str:
    # Parse user input for der_value. Expected input is "<float> <optional unit>". 
    if not der_value:
        return None
    try:
        if "kw" in der_value.lower():
            return str(float(der_value.split(" ")[0].strip()[1:]) * 1000)
        else:
            return str(float(der_value.strip()))
    except ValueError:
        gridlabd.error(f"DER_VALUE not in valid format.")

def on_init(t):
    obj_list = gridlabd.get("objects")
    der_value = parse_user_DER(gridlabd.get_global("DER_VALUE"))
    violation_rating = gridlabd.get_global("VIOLATION_RATING")
    for obj in obj_list:
        # Iterate through all objects and set needed values based on its class. 
        data = gridlabd.get_object(obj)
        if is_load(data):
            if der_value and gridlabd.get_value(obj, "DER_value") == "+0+0i VA": 
                # Set the DER_value of a load if it is 0. Currently cannot differentiate between default 0 and user-set 0. 
                gridlabd.set_value(obj, "DER_value", der_value)
        if is_node(data):
            # Might need to do something to nodes in the future. 
            pass
        if is_link(data):
            if violation_rating and gridlabd.get_value(obj, "violation_rating") == "+0 A":
                # Set violation rating of link if it is 0, only if violation rating is provided. 
                gridlabd.set_value(obj, "violation_rating", violation_rating)
    
    global_voltage_threshold = gridlabd.get_global("VOLTAGE_VIOLATION_THRESHOLD")
    global_voltage_fluctuation_threshold = gridlabd.get_global("VOLTAGE_FLUCTUATION_THRESHOLD")

    if (global_voltage_threshold):
        # Set default voltage threshold if exists within config.csv. 
        gridlabd.set_global("powerflow::voltage_violation_threshold", global_voltage_threshold)
    if (global_voltage_fluctuation_threshold):
        # Set global voltage fluctuation if exists within config.csv. 
        gridlabd.set_global("powerflow::voltage_fluctuation_threshold", global_voltage_fluctuation_threshold)
    return True

