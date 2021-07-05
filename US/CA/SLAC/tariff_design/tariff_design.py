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

def read_tariff(pathtocsv, tariff_counter):
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

	# does this define an object?
	tariff = gridlabd.get_object(tariff_name)
	t_name = tariff["name"]

	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')	
	month = clock.month
	day = clock.weekday()

	index1 = (month-1) * 24
	index2 = (month * 24) - 1 

	# check syntax 
	if (day == 5) or (day == 6):
		schedule = tariff_data["energyweekendschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True).str.replace('L','', regex=True)
		schedule = schedyle.str.split(pat=",",expand=True)
		schedule = schedule.iloc[index1:index2].reset_index()
	else:
		schedule = tariff_data["energyweekdayschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True).str.replace('L','', regex=True)
		schedule = schedyle.str.split(pat=",",expand=True)
		schedule = schedule.iloc[index1:index2].reset_index()

	rates = schedule.unique().sort()

	# check if this finds where time changes
	timing = schedule.ne(schedule.shift()).apply(lambda x: x.value.tolist())

	pcounter = 0
	rate_idx = 0
	type_idx = 0
	types = ["offpeak","peak"]

	if len(rates) >= 3:
		print("Implementation for >= 3 TOU rates in progress")

	else:
		for rate in rates:
			if (int(rate) - 1) == pcounter:
				for counter in range(5):
					if tariff_data["energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"rate"].isnull().values.any() == False:
						gridlabd.set_value(t_name, types[type_idx]+"_rate"+str(counter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"rate"]))
					if tariff_data["energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"max"].isnull().values.any() == False:
						gridlabd.set_value(t_name, types[type_idx]+"_tier"+str(counter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"max"]))
			else:
				pcounter = pcounter + 1

		pcounter = 0
		type_idx = type_idx + 1
 
	return timing


def tariff_billing(gridlabd, **kwargs):
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')	
	month = clock.month
	day = clock.weekday()
	hour = clock.hour
	old_time = kwargs['clock']
	hr_check = ((clock - old_time).total_seconds()) / 3600
	month_check = month - old_time.month

	bill_name = kwargs['bill_name']
	bill = gridlabd.get_object(bill_name)
	meter = gridlabd.get_object(bill["meter"])

	# calculate daily energy usage
	previous_usage = kwargs['usage']

	# Is this the correct time to set this value to 1hr?
	gridlabd.setvalue(meter["measured_real_energy_delta"],"measured_real_energy_delta", str(3600))
    
	# getting the energy for the time that passed?
	# this is not always the energy at the hour?
    energy_hr =(to_float(gridlabd.get_value(meter, measured_real_energy_delta)))/1000 #kWh

    # get previous
    timing = kwargs['timing']
    peak = timing[hour]

    # ensure that only calculated if one hour has passed
	if hr_check >= 1:
		daily_usage = previous_usage + energy_hr
		if peak == 1:
			if get_value(tariff_name, 'peak_tier0') and daily_usage <= to_float(get_value(tariff_name, 'peak_tier0')):
				rate0 = to_float(get_value(tariff_name,'peak_rate0'))
				charges = energy_hr * rate0
			elif get_value(tariff_name, 'peak_tier1') and daily_usage <= to_float(get_value(tariff_name, 'peak_tier1')):
				rate0 = to_float(get_value(tariff_name,'peak_rate0'))
				rate1 = to_float(get_value(tariff_name,'peak_rate1'))
				tier0 = (daily_usage - to_float(get_value(tariff_name, 'peak_tier0')))
				tier1 = energy_hr-tier0
				charges =  tier0 * rate0 + tier1 * rate1
			elif get_value(tariff_name, 'peak_tier2') and daily_usage <= to_float(get_value(tariff_name, 'peak_tier2')):
				rate0 = to_float(get_value(tariff_name,'peak_rate1'))
				rate1 = to_float(get_value(tariff_name,'peak_rate2'))
				tier0 = (daily_usage - to_float(get_value(tariff_name, 'peak_tier1')))
				tier1 = energy_hr-tier0
				charges =  tier0 * rate0 + tier1 * rate1
			elif get_value(tariff_name, 'peak_tier3') and daily_usage <= to_float(get_value(tariff_name, 'peak_tier3')) >:
				rate0 = to_float(get_value(tariff_name,'peak_rate2'))
				rate1 = to_float(get_value(tariff_name,'peak_rate3'))
				tier0 = (daily_usage - to_float(get_value(tariff_name, 'peak_tier2')))
				tier1 = energy_hr-tier0
				charges =  tier0 * rate0 + tier1 * rate1
			elif daily_usage > to_float(get_value(tariff_name, 'peak_tier3')):
				rate0 = to_float(get_value(tariff_name, 'peak_rate4'))
				charges = energy_hr * rate0
			else:
				rate0 = to_float(get_value(tariff_name,'peak_rate0'))
				charges = energy_hr * rate0

	else:
		print("Time passed was not a complete hour. Billing unchanged")
	
	return 
