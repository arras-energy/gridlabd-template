import os
import gridlabd
import csv
import pandas 
import datetime

def to_float(x):
	return float(x.split(' ')[0])

def to_datetime(x,format):
	return parser.parse(x)

def on_init(t):
	# downloads csv file from OpenEi database if not already downloaded
	if not os.path.exists('usurdb.csv'):
		import shutil
		import requests
    	url = "https://openei.org/apps/USURDB/download/usurdb.csv.gz"
    	filename = url.split("/")[-1]
    	fgzip = gzip.open(filename,'rb')
    	with gzip.open(filename, 'r') as f_in, open('usurdb.csv', 'wb') as f_out:
    		shutil.copyfileobj(f_in, f_out)

	return True

def read_tariff(pathtocsv,tariff_counter):
	# reads USA tariff csv
	pandas.set_option("max_rows",None)
    pandas.set_option("max_columns",None)
    data = pandas.read_csv("usurdb.csv",low_memory=False)

    # read in csv file depending on tariff counter value
    with open(pathtocsv) as fp:
        reader = csv.reader(fp, skipinitialspace=True, delimiter=",")
        next(reader)
        tariff_input = [row for row in reader]

    # get inputs from csv
    utility_name = tariff_input[tariff_counter][0]
    sector_type = tariff_input[tariff_counter][1]
    name = tariff_input[tariff_counter][2]
    region = tariff_input[tariff_counter][4]

    # parse database
    utility = data[data.utility==utility_name]
    utility_active = utility[utility["enddate"].isna()]
    mask = utility_active["name"].str.contains(name, regex=True, case=False) & utility_active["name"].str.contains(region, regex=True)
    tariff_data = utility_active[mask].reset_index()
 
    return tariff_data # returns df of associated tariff

def monthlyschedule_gen(tariff_data, tariff_name):
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')	
	month = clock.month
	day = clock.weekday()

	if (day == 5) or (day == 6):
		schedule = tariff_data["energyweekendschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True).str.replace('L','', regex=True)
		schedule = schedyle.str.split(pat=",",expand=True)
	else:
		schedule = tariff_data["energyweekdayschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True).str.replace('L','', regex=True)
		schedule = schedyle.str.split(pat=",",expand=True)

	index1 = (month-1) * 24
	index2 = (month * 24) - 1 

	rates = schedule.unique().sort()
	timing = schedule.ne(schedule.shift()).apply(lambda x: x.index.tolist())

	pcounter = 0
	rcounter = 0
	tcounter = 0
	rate_idx = 0
	type_idx = 0
	types = ["offpeak","peak"]

	if len(rates) >= 3:
		print("Implementation for >3 TOU rates in progress")

	else:
		for rate in rates:
			if int(rates[rate_idx]-1) == pcounter:
				if tariff_data["energyratestructure/period"+str(pcounter)+"/tier"+str(rcounter)+"rate"].isnull().values.any() == False:
					gridlabd.set_value(tariff_name, types[type_idx]+"_rate"+str(rcounter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(rcounter)+"rate"]))
					rcounter = rcounter + 1
				if tariff_data["energyratestructure/period"+str(pcounter)+"/tier"+str(tcounter)+"max"].isnull().values.any() == False:
					gridlabd.set_value(tariff_name, types[type_idx]+"_tier"+str(tcounter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(tcounter)+"max"]))
					tcounter = tcounter + 1
			else:
				pcounter = pcounter + 1

		pcounter = 0
		rcounter = 0
		tcounter = 0
		rate_idx = 0
		type_idx = 0

	return 


def tariff_billing(gridlabd, **kwargs):


	if hr_check == 1:
	else:
		print("Time passed was not a complete hour. Billing unchanged")

	
	return 
