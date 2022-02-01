import csv
import pandas as pd 


# Might want to parse model and output name as well. 
def parse_time(value, row, df):
    print(value, row)

def parse_time_zone(value, row, df):
    print("hi")
def parse_model_name(value, row, df):
    print("hi")
def parse_output_name(value, row, df):
    print("hi")
def parse_tariff_utility(value, row, df):
    print("hi")
def parse_tariff_sector(value, row, df):
    print("hi")
def parse_tariff_name(value, row, df):
    print("hi")
def parse_tariff_type(value, row, df):
    print("hi")
def parse_tariff_region(value, row, df):
    print("hi")
def parse_tariff_inclining_block_rate(value, row, df): 
    print("hi")
def default(value, row, df): 
    print(value)

def parse_csv_values(df):
    # Error checking done here 
    # Check for header values 
    switcher = {
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
        switcher.get(row["Header"], default)(row["Value"], index, df)

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

    # Query one at a time to better pin point error 
    print(df_tariff_index.to_string())
    df_tariff_index.query('utility == @tariff_utility', inplace = True)
    print(df_tariff_index.to_string())

    df_tariff_index.query('region == @tariff_region', inplace = True) 

   
    #df_tariff_index.query('name == @tariff_name', inplace = True)
    print(df_tariff_index.to_string())
    

    print(df_tariff_index.to_string())



    # These values are currently the same for all provided rows  
    #df_tariff_index.query('sector == @tariff_sector', inplace = True)
    #df_tariff_index.query('type == @tariff_type', inplace = True)
    #df_tariff_index.query(f'INCLINING_BLOCK_RATE == {tariff_inclining_block_rate}', inplace = True)
    #df_tariff_index.query('{sector == @tariff_sector', inplace = True)

    # TODO: Currently assumes one match 
    return df_tariff_index.index.tolist()[0]

def add_tariff_index_row(df, tariff_index):
    df2 = pd.DataFrame({"Header" : ["TARIFF_INDEX"], "Value" : [tariff_index]})
    df = pd.concat([df, df2], ignore_index = True, axis = 0)
    return df 


def main():
    config_file = "config.csv"
    tariff_index_file = "tariff_library_config.csv"
    df_tariff_index = pd.read_csv(tariff_index_file)
    df = pd.read_csv(config_file)
    parse_csv_values(df)
    tariff_index = generate_tariff_index(df, df_tariff_index)
    df = add_tariff_index_row(df, tariff_index)
    print(df.to_string())
    df.to_csv("config.csv")

if __name__ == "__main__":
    main()




    


