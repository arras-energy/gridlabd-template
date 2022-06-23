#!/usr/bin/env python3
import gridlabd 
import pandas
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
    conver_to_W = 1 
    try:
        if "kw" in der_value.lower():
            conver_to_W = 1000
        return str(float(der_value.split(" ")[0].strip().replace('"', '')) * conver_to_W)
    except ValueError:
        gridlabd.error(f"DER_VALUE not in valid format.")
def find_first_comma(value) -> int:
    for i, ch in enumerate(value):
        if ch == ",":
            return i
    return -1 

def on_init(t):
    obj_list = gridlabd.get("objects")

    is_config_exist = False
    try:
        df = pandas.read_fwf('config.csv', header=None)
        is_config_exist = True
    except FileNoteFoundError: 
        gridlabd.warning("config.csv not found. Proceeding with default values.")

    config_values = {} 
    if is_config_exist:
        for index in df.index:
            row_string = df.iloc[:,0][index]
            i = find_first_comma(row_string)
            config_values[row_string[:i]] = row_string[i+1:].strip()
        for key in config_values.keys():
            print(f"{key} : {config_values[key]}")

    der_value = parse_user_DER(config_values.get("DER_VALUE", None))
    violation_rating = config_values.get("VIOLATION_RATING", None)
    load_list = [] 
    is_set_DER_for_all = False 
    str_load_list = config_values.get("LOAD_LIST", None)
    if str_load_list:
        if str_load_list == "*" :
            is_set_DER_for_all = True
        else:
            delimeter = " "
            if "," in str_load_list:
                delimeter = ","
            load_list = [load.strip() for load in str_load_list.split(delimeter)]
                

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
    
    global_voltage_threshold = config_values.get("VOLTAGE_VIOLATION_THRESHOLD", None)
    global_voltage_fluctuation_threshold = config_values.get("VOLTAGE_FLUCTUATION_THRESHOLD", None)

    if (global_voltage_threshold):
        # Set default voltage threshold if exists within config.csv. 
        gridlabd.set_global("powerflow::voltage_violation_threshold", global_voltage_threshold)
    if (global_voltage_fluctuation_threshold):
        # Set global voltage fluctuation if exists within config.csv. 
        gridlabd.set_global("powerflow::voltage_fluctuation_threshold", global_voltage_fluctuation_threshold)
    return True

