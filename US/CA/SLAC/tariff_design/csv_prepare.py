import csv
import pandas as pd 
import re
import gridlabd 
import datetime 
from dateutil import parser 


df_column_one_name = "Header" # config.csv column one name 
df_column_two_name = "Value" # config.csv column two name 
config_file = "config.csv" # name of config file 
tariff_index_file = "tariff_library_config.csv" # name of tariff config file 


def parse_weather(value, row, df,tariff_index_file):
    """ Currently needs to be implemented. 
    """

    print("hi")
def parse_time(value, row, df,tariff_index_file):
    """ Parses time value in ISO8601 or YYYY-MM-DD DD:HH:MM TZN. Latter format will throw a warning.

    """
    print(parser.parse(value))
    if re.match("^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9] [A-Z]{3}$", value) == None:
        print("bad time")

def parse_time_zone(value, row, df,tariff_index_file):
    """ Parses time zone value with any three capital letters followed by a "+", a number, and any three more capital letters. 
    
    Example: EST+5EDT
    """
    if re.match("^[A-Z]{3}\+[1-9][A-Z]{3}$", value) == None:
        print("bad")
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
    """ TODO: Levenshtein distance
    """
    unique_utility = tariff_index_file.utility.unique()
    if not value in unique_utility:
        gridlabd.warning(f"{value} not recognized. Will attempt to generate tariff configuration.\nOnly {unique_utility} are accepted.")
def parse_tariff_sector(value, row, df,tariff_index_file):
    """ Currently not needed and is just a function stub.
    """
    raise NotImplementedError
def parse_tariff_name(value, row, df,tariff_index_file):
    """ Matches value with names in tariff configuration file. 
    """
    unique_tariff_name = tariff_index_file.name.unique()
    if not value in unique_tariff_name:
        gridlabd.warning(f"{value} not recognized. Will attempt to generate tariff configuration\nOnly {unique_tariff_name} are accepted.")
def parse_tariff_type(value, row, df,tariff_index_file):
    """ Currently not needed and is just a function stub.
    """
    raise NotImplementedError
# Only takes in a few values. 
def parse_tariff_region(value, row, df,tariff_index_file):
    """ Matches value with regions in tariff configuration file. 
    """
    unique_tariff_region = tariff_index_file.region.unique()
    if not value in unique_tariff_region:
        gridlabd.warning(f"{value} not recognized. Will attempt to generate tariff configuration\nOnly {unique_tariff_region} are accepted.")
def parse_tariff_inclining_block_rate(value, row, df,tariff_index_file): 
    raise NotImplementedError
def default(value, row, df,tariff_index_file): 
    """ Handles unsupported values 
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
    "TARIFF_INCLINING_BLOCK_RATE":parse_tariff_inclining_block_rate
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
    df_copy = df_tariff_index.copy(deep=True)
    # Query one at a time and preserves last dataframe that had values. 
    if (tariff_utility != ""):
        df_copy = df_tariff_index.query('utility == @tariff_utility', inplace = False)
        if (len(df_copy) > 0):
            df_tariff_index = df_copy.copy(deep=False)
    if (tariff_region != ""):
        df_copy = df_tariff_index.query('region == @tariff_region', inplace = False) 
        if (len(df_copy) > 0):
            df_tariff_index = df_copy.copy(deep=False)
    if (tariff_name != ""):
        df_copy = df_tariff_index.query('name == @tariff_name', inplace = False)
        if (len(df_copy) > 0):
            df_tariff_index = df_copy.copy(deep=False)

    # Testing with indexes
    #df_tariff_index['row_num'] = df_tariff_index.index;
    #df_tariff_index.set_index(["utility","name", "region"],inplace=True)
    #df_tariff_index = df_tariff_index.loc[tariff_utility][["row_num"]]
    #df_tariff_index = df_tariff_index.loc[tariff_utility]
    #if (len(df_tariff_index.index) == 1):
        #return df_tariff_index["row_num"]
    #else:
        #print(df_tariff_index.index.get_level_values(0))
        #return -1 

    if (len(df_tariff_index)==1):
        return df_tariff_index.index.tolist()[0]
    else:
        raise ValueError(f"\nInputs did not correspond to unique tariff configuration."\
            " Please add information to input from values below.\n"\
            "Corresponding header values are TARIFF_UTILITY, TARIFF_REGION, TARIFF_NAME\n" + df_tariff_index[["utility","region","name"]].to_string())
        



    


    # These values are currently the same for all provided rows  
    #df_tariff_index.query('sector == @tariff_sector', inplace = True)
    #df_tariff_index.query('type == @tariff_type', inplace = True)
    #df_tariff_index.query(f'INCLINING_BLOCK_RATE == {tariff_inclining_block_rate}', inplace = True)
    #df_tariff_index.query('{sector == @tariff_sector', inplace = True)

    # TODO: Currently assumes one match 
    

def add_tariff_index_row(df, tariff_index):
    """ Appends "TARIFF_INDEX" on to config.csv along with its value.
    """
    df2 = pd.DataFrame({df_column_one_name : ["TARIFF_INDEX"], df_column_two_name : [tariff_index]})
    df = pd.concat([df, df2], ignore_index = True, axis = 0)
    return df 


def main():

    try:
        df_tariff_index = pd.read_csv(tariff_index_file)
    except FileNotFoundError:
        gridlabd.error(f"{tariff_index_file} file not found")
    except pd.errors.EmptyDataError:
        gridlabd.error(f"{tariff_index_file} file empty")

    gridlabd.output(f"Reading input {config_file}...")

    try:
        df = pd.read_csv(config_file)
    except FileNotFoundError:
        gridlabd.error(f"{config_file} file not found")
    except pd.errors.EmptyDataError:
        gridlabd.error(f"{config_file} file not found")

    try:
        is_column_names_valid(df)
        parse_csv_values(df,df_tariff_index)
        df = add_tariff_index_row(df,generate_tariff_index(df, df_tariff_index))
    except ValueError as e:
        gridlabd.error(str(e))

    print(df.to_string())
    df.to_csv("config.csv", index = False)

if __name__ == "__main__":
    main()




    


