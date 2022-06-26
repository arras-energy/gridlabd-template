#!/usr/bin/env python3
import gridlabd 
from csv import reader
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

def on_init(t):
    # List of all objects for model processing. 
    obj_list = gridlabd.get("objects")

    # Dictionary of config.csv values. First column maps to second column.
    config_values = {} 

    # The list of loads to set DER_value. 
    load_list = [] 

    # Boolean to indicate of all loads' DER_value should be set. 
    is_set_DER_for_all = False

    # Set of loads to set DER_VALUE. 
    load_set = set()
    try:
        with open('config.csv', 'r') as read_obj:
            csv_reader = reader(read_obj)
            for row in csv_reader:
                if row[0] == "LOAD_LIST":
                    # Splits load list value into a list using "," or " "
                    if row[1].strip() == "*" :
                        # Star indicates all loads should be set. 
                        is_set_DER_for_all = True
                    elif len(row) == 2:
                        load_set = set([load.strip() for load in row[1].split()])
                    else:
                        load_set = set([load.strip() for load in row[1:]])
                else:
                    # Put key-value into dictonary for all other rows. 
                    config_values[row[0]] = row[1].strip()
    except FileNotFoundError:
        gridlabd.warning("config.csv not found. Proceeding with default values.")


    # Converts number to W if units kW provided.
    der_value = config_values.get("DER_VALUE", None)

    if (not load_set and der_value):
        gridlabd.warning("DER_VALUE provided with no loads specified.")

    violation_rating = config_values.get("VIOLATION_RATING", None)

    for obj in obj_list:
        # Iterate through all objects and set needed values based on its class. 
        data = gridlabd.get_object(obj)
        if is_load(data):
            if (der_value and data["name"] in load_set) or is_set_DER_for_all: 
                # Set the DER_value of a load if listed or "*".
                gridlabd.set_value(obj, "DER_value", der_value)
                print(f'{data["name"]} DER : {gridlabd.get_value(obj, "DER_value")}')
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

