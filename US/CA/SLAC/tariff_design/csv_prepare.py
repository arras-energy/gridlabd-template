import csv
import pandas as pd 
import re
import gridlabd 
import datetime 
from dateutil import parser 
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sys
# figure out gridlabd warning with gridlabd.set_global 
# maybe check start time with end time. 
# try to move stuff to openfido/tariff_design afterwards
# submit application to gridabld 
# currently row index 1,5,6,8 isn't active in OpenEI, 3,7  requires more specificaiton, only 0,2,4,9 works
# check power - line 274
# add verbose and stuff
# TODO: catch exception in Jewel's cdoe

df_column_one_name = "Header" # config.csv column one name 
df_column_two_name = "Value" # config.csv column two name 
config_file = "config.csv" # name of config file 
tariff_index_file = "tariff_library_config.csv" # name of tariff config file 
verbose = True

def print_verbose(msg):
    if verbose:
        print("VERBOSE [TARIFF_DESIGN] : " + msg)


def parse_weather(value, row, df,tariff_index_file):
    """ Parses weather station index for the command "gridlabd weather index {value}" dont in openfido.sh. Prints warning if can not parse.
    """
    if re.match("[A-Z]{2}(-[A-Z][a-z]*(_[A-Z][a-z]*)*)?$", value) == None:
        gridlabd.warning(f"{value} could not be parsed. On failure, check below for list of case sensitive, matching weather stations."\
            " On success, ignore this message.")
    
def parse_time(value, row, df,tariff_index_file):
    """ Parses time value in ISO8601 or YYYY-MM-DD DD:HH:MM TZN. Raises exception if can not parse. 

    """
    parser.parse(value)

def parse_time_zone(value, row, df,tariff_index_file):
    """ Parses time zone value with any three capital letters followed by a "+", a number, and any three more capital letters. Raises exception. 
    
    Example: EST+5EDT
    """
    if re.match("^[A-Z]{3}\+[1-9][A-Z]{3}$", value) == None:
        raise ValueError("Could not parse time zone")
def parse_model_name(value, row, df,tariff_index_file):
    """ Parses name of model. Appends .glm if not present at end of string.
    """
    if not value.endswith('.glm'):
        gridlabd.warning("Model name should end with .glm. Adding .glm...")
        df.at[row, df_column_two_name] = value + ".glm"
def parse_output_name(value, row, df,tariff_index_file):
    """ Parses name of output file. Appends .csv if not present at the end of string. 
    """
    if not value.endswith('.csv'):
        gridlabd.warning("Output name should end with .csv Adding .csv...")
        df.at[row, df_column_two_name] = value + ".csv"

def parse_tariff_utility(value, row, df,tariff_index_file):
    """ Parses tariff_utility based on tariff configuration csv file. Supports fuzzy string matching. Raises exception if multiple matches/none.
    """
    utility_match_ratio = 85
    utility_match_perfect_ratio = 100
    unique_utility = tariff_index_file.utility.unique()
    best_matches = process.extract(value, unique_utility) # returns the best match in [0] and score in [1]
    match_list = [] 
    for match, score in best_matches:
        if score == utility_match_perfect_ratio: # perfect match means no need to look at others
            df.at[row, df_column_two_name] = match 
            return
        if score > utility_match_ratio:
            match_list.append(match)
    if len(match_list) == 1:
        df.at[row, df_column_two_name] = match_list[0]
        print_verbose(f"Found suitable match for {value} which has been replaced with {match_list[0]}")
    elif len(match_list) > 1:
        raise ValueError(f"Found multiple matches for {value}. Please specify from the list below:\n{match_list}")
    else:
        raise ValueError(f"Could not match {value} with elements in {unique_utility}.")


    #if best_match[1] > 80:
        #df.at[row, df_column_two_name] = best_match[0]
    #else:
        #
def parse_tariff_sector(value, row, df,tariff_index_file):
    """ Currently not needed and is just a function stub.
    """
    raise NotImplementedError
def parse_tariff_name(value, row, df,tariff_index_file):
    """ Parses tariff_name based on tariff configuration csv file. Supports fuzzy string matching. Raises exception if multiple matches/none. 
    """
    name_match_ratio = 85
    name_match_perfect_ratio = 100
    unique_tariff_name = tariff_index_file.name.unique()
    best_matches = process.extract(value, unique_tariff_name) # returns the best match in [0] and score in [1]
    match_list = []
    for match, score in best_matches:
        if score == name_match_perfect_ratio:
            df.at[row, df_column_two_name] = match
            return
        if score > name_match_ratio:
            match_list.append(match)
    if len(match_list) == 1:
        df.at[row, df_column_two_name] = match_list[0]
        print_verbose(f"Found suitable match for {value} which has been replaced with {match_list[0]}")
    elif len(match_list) > 1:
        raise ValueError(f"Found multiple matches for {value}. On success, ignore warning. On failure, please specify from the list below:\n{match_list}")
    else:
        raise ValueError(f"Could not match {value} with elements in {unique_tariff_name}.")
def parse_tariff_type(value, row, df,tariff_index_file):
    """ Currently not needed and is just a function stub.
    """
    raise NotImplementedError
# Only takes in a few values. 
def parse_tariff_region(value, row, df,tariff_index_file):
    """ Parses tariff_region based on tariff configuration csv file. Supports fuzzy string matching. Raises exception if multiple matches/none. 
    """
    region_match_ratio = 90
    region_match_perfect_ratio = 100
    unique_tariff_region = tariff_index_file.region.unique()
    best_matches = process.extract(value, unique_tariff_region) # returns the best match in [0] and score in [1]
    match_list = []
    for match, score in best_matches:
        if score == region_match_perfect_ratio:
            df.at[row, df_column_two_name] = match
            return
        if score > region_match_ratio:
            match_list.append(match)
    if len(match_list) == 1:
        df.at[row, df_column_two_name] = match_list[0]
        print_verbose(f"Found suitable match for {value} which has been replaced with {match_list[0]}")
    elif len(match_list) > 1:
        raise ValueError(f"Found multiple matches for {value}. Please specify from the list below:\n{match_list}")
    else:
        raise ValueError(f"Could not match {value} with elements in {unique_tariff_region}.")
def parse_tariff_inclining_block_rate(value, row, df,tariff_index_file): 
    raise NotImplementedError

def parse_tariff_index_specific(value, row, df, tariff_index_file):
    if (not value.isdigit()):
        raise ValueError(f"{value} must be an integer.")
def parse_verbose(value,row,df,tariff_index_file):
    verbose = (value == 'True')
def default(value, row, df,tariff_index_file): 
    """ Handles unsupported values. Raises warning. 
    """
    gridlabd.warning(f"({df.at[row, df_column_one_name]}, {value}) on row {row} not supported")

def parse_csv_values(df,tariff_index_file):
    """ Loops through df and calls parsing functions based on its corresponding label. 
    """
    switcher = {
    "WEATHER_STATION": parse_weather,
    "STARTTIME": parse_time,
    "STOPTIME": parse_time,
    "TIMEZONE": parse_time_zone,
    "MODEL": parse_model_name,
    "OUTPUT": parse_output_name,
    "TARIFF_UTILITY": parse_tariff_utility,
    "TARIFF_SECTOR": parse_tariff_sector,
    "TARIFF_NAME": parse_tariff_name,
    "TARIFF_TYPE": parse_tariff_type,
    "TARIFF_REGION":parse_tariff_region,
    "TARIFF_INCLINING_BLOCK_RATE":parse_tariff_inclining_block_rate,
    "TARIFF_INDEX_SPECIFIC":parse_tariff_index_specific,
    }
    for index, row in df.iterrows():
        df.at[index, df_column_two_name] = row[df_column_two_name].strip()
        try:
            switcher.get(row[df_column_one_name], default)(row[df_column_two_name], index, df,tariff_index_file) # second parethesis provides arguments to functions
        except ValueError as e:
            raise
def is_column_names_valid(df):
    """ Checks the first row of df to make sure column 1 is "Header" and column 2 is "Value"
    """
    if len(df.columns) != 2 or df.columns[0] != df_column_one_name or df.columns[1] != df_column_two_name:
        raise ValueError(f"{config_file} column headers must be 'Header' and 'Value'")
    


def generate_tariff_index(df, df_tariff_index):
    """ Generates tariff index (row number in tariff_config) based on matching values of df (config.csv) and df_tariff_index
    """
    def raise_tariff_index_error():
        raise ValueError(f"Tariff inputs did not result in unique value. Please replace values TARIFF_UTILITY, TARIFF_REGION, TARIFF_NAME with the closest matches listed below."\
                + " Empty list indicates no closest matches.\n" + df_tariff_index[["utility","region","name"]].to_string())

    tariff_utility = ""
    tariff_sector = ""
    tariff_name = ""
    tariff_type = ""
    tariff_region = ""
    tariff_inclining_block_rate = ""
    for index, row in df.iterrows():
        if (row[df_column_one_name] == "TARIFF_UTILITY"):
            tariff_utility = row[df_column_two_name] 
        if (row[df_column_one_name] == "TARIFF_SECTOR"):
            tariff_sector = row[df_column_two_name]
        if (row[df_column_one_name] == "TARIFF_NAME"):
            tariff_name = row[df_column_two_name]
        if (row[df_column_one_name] == "TARIFF_TYPE"):
            tariff_type = row[df_column_two_name]
        if (row[df_column_one_name] == "TARIFF_REGION"):
            tariff_region = row[df_column_two_name]
        if (row[df_column_one_name] == "TARIFF_INCLINING_BLOCK_RATE"):
            tariff_inclining_block_rate = row[df_column_two_name]

    # In case of white spaces
    df_tariff_index.columns = [column.replace(" ", "") for column in df_tariff_index.columns]
    
    # If field is provided, quries tariff configuration file. Raises error if not found. 
    df_copy = df_tariff_index
    if (tariff_utility != ""):
        df_copy = df_tariff_index.query('utility == @tariff_utility', inplace = False)
        if (len(df_copy) == 0):
            raise_tariff_index_error()
        df_tariff_index = df_copy
    if (tariff_region != ""):
        df_copy = df_tariff_index.query('region == @tariff_region', inplace = False) 
        if (len(df_copy) == 0):
            raise_tariff_index_error()
        df_tariff_index = df_copy
    if (tariff_name != ""):
        df_copy = df_tariff_index.query('name == @tariff_name', inplace = False)
        if (len(df_copy) == 0):
            raise_tariff_index_error()
        df_tariff_index = df_copy

    # df_tariff_index['TARIFF_INDEX'] = df_tariff_index.index;
    # df_tariff_index.set_index(["utility","name", "region"],inplace=True)
    # df_tariff_index = df_tariff_index.loc[(tariff_utility, tariff_name, tariff_region), "TARIFF_INDEX"]
    # print(df_tariff_index.to_string())
    
    # #df_tariff_index = df_tariff_index.loc[tariff_name][["TARIFF_INDEX"]]
    # if (len(df_tariff_index.index) == 1):
    #     return df_tariff_index["TARIFF_INDEX"]
    # else:
    #     print(df_tariff_index.index.get_level_values(0))
    #     return -1 

    if (len(df_tariff_index) > 1):
        raise_tariff_index_error()
    return df_tariff_index.index.tolist()[0]
        



    


    # These values are currently the same for all provided rows  
    #df_tariff_index.query('sector == @tariff_sector', inplace = True)
    #df_tariff_index.query('type == @tariff_type', inplace = True)
    #df_tariff_index.query(f'INCLINING_BLOCK_RATE == {tariff_inclining_block_rate}', inplace = True)
    #df_tariff_index.query('{sector == @tariff_sector', inplace = True)

    

def add_tariff_index_row(df, tariff_index):
    """ Appends "TARIFF_INDEX" on to config.csv along with its value.
    """
    df2 = pd.DataFrame({df_column_one_name : ["TARIFF_INDEX"], df_column_two_name : [tariff_index]})
    df = pd.concat([df, df2], ignore_index = True, axis = 0)
    return df 


def main():
    #gridlabd.set_global("suppress_repeat_messages","FALSE")
    print_verbose(f"Reading {tariff_index_file} file...")
    try:
        df_tariff_index = pd.read_csv(tariff_index_file)
    except FileNotFoundError:
        gridlabd.error(f"{tariff_index_file} file not found")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        gridlabd.error(f"{tariff_index_file} file empty")
        sys.exit(1)
    print_verbose(f"Read {tariff_index_file} file success.")

    print_verbose(f"Reading {config_file} file...")
    try:
        df = pd.read_csv(config_file)
    except FileNotFoundError:
        gridlabd.error(f"{config_file} file not found")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        gridlabd.error(f"{config_file} file not found")
        sys.exit(1)
    print_verbose(f"Read {config_file} file success.")


    try:
        print_verbose("Checking column names...")
        is_column_names_valid(df)
        print_verbose("Check column names sucess.")

        print_verbose(f"Parsing {config_file} column values...")
        parse_csv_values(df,df_tariff_index)
        print_verbose(f"Parse {config_file} column values success")

        print_verbose(f"Generating TARIFF_INDEX...")
        df = add_tariff_index_row(df,generate_tariff_index(df, df_tariff_index))
        print_verbose(f"TARIFF_INDEX generation success")
    except ValueError as e:
        gridlabd.error(str(e))
        sys.exit(1)
    df.to_csv("config.csv", index = False)

if __name__ == "__main__":
    main()




    


