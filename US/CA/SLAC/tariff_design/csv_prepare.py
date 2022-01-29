import csv
import pandas as pd 



def parse_start_time(value, row, df):
    print(value, row)
    df.at[row,"Value"] = "poop"
def parse_stop_time(value, row, df):
    print("hi")
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





def main():
    config_file = "config.csv"
    df = pd.read_csv(config_file)
   

   

    switcher = {
    "STARTTIME": parse_start_time,
    "STOPTIME": parse_stop_time,
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

    df.to_csv("asdf.csv")

if __name__ == "__main__":
    main()




    


