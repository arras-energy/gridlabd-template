import csv
import pandas as pd 
import re


# Parses weather station value. Checks for no spaces, capitalization, 
def parse_weather(value, row, df,tariff_index_file):
    print("hi")
def parse_time(value, row, df,tariff_index_file):
    if re.match("^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9] [A-Z]{3}$", value) == None:
        print("bad time")
# Matches exactly for now 
def parse_time_zone(value, row, df,tariff_index_file):
    if re.match("^[A-Z]{3}\+[1-9][A-Z]{3}$", value) == None:
        print("bad")
# Parses model name value. Makes sure there is .glm at the end. 
def parse_model_name(value, row, df,tariff_index_file):
    if not value.endswith('.glm'):
        print("adding glm to model name...")
        df.at[row, "Value"] = value + ".glm"
# Parses output name value. Makes sure there is .csv at the end. 
def parse_output_name(value, row, df,tariff_index_file):
    if not value.endswith('.csv'):
        print("adding csv to output name...")
        df.at[row, "Value"] = value + ".csv"
# could do levenshtein distance
def parse_tariff_utility(value, row, df,tariff_index_file):
    unique_utility = tariff_index_file.utility.unique()
    if value in unique_utility:
        print(value)
    else:
        print("bye")
def parse_tariff_sector(value, row, df,tariff_index_file):
    print("Currently unnecessary")
# Only takes in a few values. 
def parse_tariff_name(value, row, df,tariff_index_file):
    print("hi")
def parse_tariff_type(value, row, df,tariff_index_file):
    print("Currently unnecessary")
# Only takes in a few values. 
def parse_tariff_region(value, row, df,tariff_index_file):
    print("hi")
def parse_tariff_inclining_block_rate(value, row, df,tariff_index_file): 
    print("Currently unnecessary")
def default(value, row, df,tariff_index_file): 
    print(value)

def parse_csv_values(df,tariff_index_file):
    # Error checking done here 
    # Check for header values 
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
        switcher.get(row["Header"], default)(row["Value"], index, df,tariff_index_file)

def generate_tariff_index(df, df_tariff_index):
    # Loop through df again and find the tariff values. Match them with df_tariff_index
    tariff_utility = ""
    tariff_sector = ""
    tariff_name = ""
    tariff_type = ""
    tariff_region = ""
    tariff_inclining_block_rate = ""
    for index, row in df.iterrows():
        if (row["Header"] == "TARIFF_UTILITY"):
            tariff_utility = row["Value"] 
            print(tariff_utility)
        if (row["Header"] == "TARIFF_SECTOR"):
            tariff_sector = row["Value"]
            print(tariff_sector)
        if (row["Header"] == "TARIFF_NAME"):
            tariff_name = row["Value"]
            print(tariff_name)
        if (row["Header"] == "TARIFF_TYPE"):
            tariff_type = row["Value"]
            print(tariff_type)
        if (row["Header"] == "TARIFF_REGION"):
            tariff_region = row["Value"]
            print(tariff_region)
        if (row["Header"] == "TARIFF_INCLINING_BLOCK_RATE"):
            tariff_inclining_block_rate = row["Value"]
            print(tariff_inclining_block_rate)

    # In case of white spaces
    df_tariff_index.columns = [column.replace(" ", "") for column in df_tariff_index.columns]
    df_copy = df_tariff_index.copy(deep=True)
    # Query one at a time to better pin point error 
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
        df_tariff_index[["utility","region","name"]].to_csv("error.csv", index = False)
        return -1



    


    # These values are currently the same for all provided rows  
    #df_tariff_index.query('sector == @tariff_sector', inplace = True)
    #df_tariff_index.query('type == @tariff_type', inplace = True)
    #df_tariff_index.query(f'INCLINING_BLOCK_RATE == {tariff_inclining_block_rate}', inplace = True)
    #df_tariff_index.query('{sector == @tariff_sector', inplace = True)

    # TODO: Currently assumes one match 
    

def add_tariff_index_row(df, tariff_index):
    df2 = pd.DataFrame({"Header" : ["TARIFF_INDEX"], "Value" : [tariff_index]})
    df = pd.concat([df, df2], ignore_index = True, axis = 0)
    return df 


def main():
    config_file = "config.csv"
    tariff_index_file = "tariff_library_config.csv"
    try:
        df_tariff_index = pd.read_csv(tariff_index_file)
    except FileNotFoundError:
        print(f"{tariff_index_file} not found.")
    except pd.errors.EmptyDataError:
        print(f"No data in {tariff_index_file}")
    try:
        df = pd.read_csv(config_file)
    except FileNotFoundError:
        print(f"{config_file} not found.")
    except pd.errors.EmptyDataError:
        print(f"No data in {config_file}")

    parse_csv_values(df,df_tariff_index)
    print(df_tariff_index)
    tariff_index = generate_tariff_index(df, df_tariff_index)
    if (tariff_index == -1):
        return
    df = add_tariff_index_row(df, tariff_index)
    print(df.to_string())
    df.to_csv("config.csv", index = False)

if __name__ == "__main__":
    main()




    


