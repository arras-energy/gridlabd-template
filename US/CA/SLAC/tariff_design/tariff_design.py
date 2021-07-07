import os
import gridlabd
import csv
import pandas 
import datetime
from dateutil import parser

RATE_FLAG = TRUE 

def to_float(x):
	return float(x.split(' ')[0])

def to_datetime(x,format):
	return parser.parse(x)

def on_init(t):

	# downloads csv file from OpenEi database if not already downloaded
	if not os.path.exists('usurdb.csv'):
		print("Downloading needed csv file to working directory")
		# needed libraries
		import shutil
		import requests
		import gzip
		# url from OpenEi database
    	url = "https://openei.org/apps/USURDB/download/usurdb.csv.gz"
    	filename = url.split("/")[-1]
    	fgzip = gzip.open(filename,'rb')
    	# gets .gz file from OpenEi database
    	with open(filename, "wb") as f:
            r = requests.get(url)
            f.write(r.content) 
        # unzips .gz file    
    	with gzip.open(filename, 'r') as f_in, open('usurdb.csv', 'wb') as f_out:
    		shutil.copyfileobj(f_in, f_out)

    # IS THIS CORRECT TO SET DELTA TO 1 HR
	meter = gridlabd.get_object("meter")
	delta = to_float(gridlabd.get_value(meter["measured_energy_delta_timestep"],"measured_energy_delta_timestep"))
	if delta != 3600
		print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
		gridlabd.setvalue(meter["measured_energy_delta_timestep"],"measured_energy_delta_timestep", str(3600))

	return True

def read_tariff(pathtocsv, tariff_counter):
	# reads USA tariff csv usurdb.csv from OpenEi
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

    # Inclining rate flag
    global RATE_FLAG 
    RATE_FLAG = tariff_input[tariff_counter][5]

    # parse database
    utility = data[data.utility==utility_name]
    utility_active = utility[utility["enddate"].isna()]
    mask = utility_active["name"].str.contains(name, regex=True, case=False) & utility_active["name"].str.contains(region, regex=True) & utility_active["sector"].str.contains(sector_type, regex=True, case=False)
    tariff_data = utility_active[mask].reset_index()

    # SETS ALL NaN to 0.0
    tariff_data.fillna(0.0, inplace=True)
 
    return tariff_data # returns df of associated tariff

def monthlyschedule_gen(tariff_data): #Inputs tariff df from csv and populated tariff gridlabd obj

	# Finding default tariff obj name from gridlabd	
	tariff = gridlabd.get_object("tariff")
	t_name = tariff["name"]

	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')	
	month = clock.month
	day = clock.weekday()

	index1 = (month-1) * 24
	index2 = (month * 24) - 1 

	# check syntax 
	if (day == 5) or (day == 6):
		schedule = tariff_data["energyweekendschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True).str.replace('L','', regex=True)
		schedule = schedule.str.split(pat=",",expand=True)
		schedule = schedule.iloc[0,index1:index2].astype(int).tolist()
	else:
		schedule = tariff_data["energyweekdayschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True).str.replace('L','', regex=True)
		schedule = schedule.str.split(pat=",",expand=True)
		schedule = schedule.iloc[0,index1:index2].astype(int).tolist()

	rates = list(set(schedule))

	# gives index in schedule where rate changes
	c = [i for i in range(1,len(schedule)) if schedule[i]!=schedule[i-1] ]
	timing = list(range(c[0],c[1]))

	pcounter = 0
	rate_idx = 0
	type_idx = 0
	types = ["offpeak","peak"]

	# fills in tariff obj with peak and offpeak rates
	if len(rates) >= 3:
		print("Implementation for >= 3 TOU rates per day in progress")
	else:
		for rate in rates:
			while rate != pcounter:
				pcounter = pcounter + 1
			else:
				for counter in range(4):
					# SETS ALL OBJ PROPERTIES FOR TIER 0-3 AND RATES 0-3
					# CHECK SYNTAX
					gridlabd.set_value(t_name, types[type_idx]+"_rate"+str(counter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"rate"]))
					gridlabd.set_value(t_name, types[type_idx]+"_tier"+str(counter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"max"]))

				# SETS ALL OBJ PROPERTY FOR RATE 4
				gridlabd.set_value(t_name, types[type_idx]+"_rate"+str(counter+1), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter+1)+"rate"]))

		pcounter = 0
		type_idx = type_idx + 1
 
	return timing

def on_commit(**kwargs, t):
	# CHECK IF THIS INPUT WORKS WITH FUNCTION

	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')	
	time = clock.time
	billing_days = (((kwargs['clock']).time + time) / 86400) # in days but could convert to make billing hours property

	if time % 3600 == 0: #checks if top of the hour will this be an issue if two hours pass?

		path = kwargs['pathtocsv']
		t_counter = kwargs['tariff_counter']
		tariff_df = read_tariff(path, t_counter)
		timing = monthlyschedule_gen(tariff_df)

		bill = gridlabd.get_object("test_bill")
		meter = gridlabd.get_object(bill["meter"])

		# calculate previous daily energy usage
		previous_usage = kwargs['usage']
	    
	    # energy usage over the hour
	    energy_hr =(to_float(gridlabd.get_value(meter, measured_real_energy_delta)))/1000 #kWh

	    # check if current time during peak rate
	    timing = kwargs['timing']
	    if hour in timing:
	    	peak = 1

	    global RATE_FLAG

	    if RATE_FLAG = TRUE:
			daily_usage = previous_usage + energy_hr
			if peak == 1:
				string = 'peak'
			else:
				string = "offpeak"

			for counter in range(4):
					tier[counter] = to_float(gridlabd.get_value(tariff_name, string+'_tier'+str(counter)))
					rate[counter] = to_float(get_value(tariff_name, string+'_rate'+str(counter)))

			rate[counter+1] = to_float(get_value(tariff_name, string+'_rate'+str(counter+1)))
			
			tier0 = max(min(daily_usage, tier[0]) - previous_usage, 0) 
			tier1 = max(min(daily_usage, tier[1]) - previous_usage - tier0, 0)
			tier2 = max(min(daily_usage, tier[2]) - previous_usage - tier0 - tier1, 0)
			tier3 = max(min(daily_usage, tier[3]) - previous_usage - tier0 - tier1 - tier3, 0)
			tier4 = max(energy_hr - tier0 - tier1 - tier3, 0)

			hr_charge = rate[0]*tier0+rate[1]*tier1+rate[2]*tier2+rate[3]*tier3+rate[4]*tier4
			gridlabd.set_value(bill_name,"total_charges",str(to_float(bill["total_charges"])+hr_charge))
			gridlabd.set_value(bill_name,"billing_days",str(billing_days))
		
	    else:
	    	print("Implementation for non-inclining block rate in progress") 

	else:
		print("Time passed was not a complete hour. Billing unchanged")

	return gridlabd.NEVER