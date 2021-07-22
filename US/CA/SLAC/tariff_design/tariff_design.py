import os
import gridlabd
import csv
import pandas 
import datetime
from dateutil import parser

def to_float(x):
	return float(x.split(' ')[0])

def to_datetime(x,format):
	return parser.parse(x)

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
	df = utility_active[mask].reset_index()

	if df.shape[0] > 1:
		print("Not enough information provided to define tariff: ", df.shape[0]," tariffs generated.")
		for i in range(df.shape[0]):
			print("Index",i,": ", df.iloc[i,3]) # print df name
		idx = int(input("Enter desired tariff index: "))
		tariff_data = pandas.DataFrame(data=df.iloc[[idx]]).reset_index(drop=True)
		# This is currently rasiing errors in docker?
	elif df.shape[0] == 0:
		raise Exception("No active tariff found in OpenEi database matching information. Simulation ending") 
		# there are other methods to exit simulation but this makes sense
	else:
		tariff_data = df

	# SETS ALL NaN to 0.0
	tariff_data.fillna(0.0, inplace=True)

	return tariff_data # returns df of associated tariff

def monthlyschedule_gen(tariff_data): #Inputs tariff df from csv and populates tariff gridlabd obj

	# Finding default tariff obj name from gridlabd	
	tariff = gridlabd.get_object("tariff")
	tariff_name = tariff["name"]

	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')	
	month = clock.month
	day = clock.weekday()

	index1 = (month-1) * 24
	index2 = (month * 24)

	# check syntax 
	global schedule
	if (day == 5) or (day == 6):
		
		schedule = tariff_data["energyweekendschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True).str.replace('L','', regex=True)
		schedule = schedule.str.split(pat=",",expand=True)
		schedule = schedule.iloc[0,index1:index2].astype(int).tolist()
	else:
		schedule = tariff_data["energyweekdayschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True).str.replace('L','', regex=True)
		schedule = schedule.str.split(pat=",",expand=True)
		schedule = schedule.iloc[0,index1:index2].astype(int).tolist()

	lookup = set()
	global rates
	rates = [x for x in schedule if x not in lookup and lookup.add(x) is None]

	# Changing rates definition to fix peak vs offpeak def 
	# rates = list(set(schedule))
	# gives index in schedule where rate changes
	#c = [i for i in range(1,len(schedule)) if schedule[i]!=schedule[i-1] ]
	#timing = list(range(c[0],c[1]))

	# fills in tariff obj with peak and offpeak rates
	if len(rates) > 3:
		print("Implementation for > 3 TOU rates per day in progress")
	elif len(rates) == 3: # handles 3 rates per day
		pcounter = 0
		type_idx = 0
		types = ["offpeak","shoulder","peak"]
		for rate in rates:
			while rate != pcounter:
				pcounter = pcounter + 1
			else:
				for counter in range(4):
					# SETS ALL OBJ PROPERTIES FOR TIER 0-3 AND RATES 0-3
					gridlabd.set_value(tariff_name, types[type_idx]+"_rate"+str(counter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"rate"]))
					gridlabd.set_value(tariff_name, types[type_idx]+"_tier"+str(counter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"max"]))

				# SETS ALL OBJ PROPERTY FOR RATE 4
				gridlabd.set_value(tariff_name, types[type_idx]+"_rate"+str(counter+1), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter+1)+"rate"]))

				pcounter = 0
				type_idx = type_idx + 1
	else: # handles 1-2 rates per day
		pcounter = 0
		type_idx = 0
		types = ["offpeak","peak"]
		for rate in rates:
			while rate != pcounter:
				pcounter = pcounter + 1
			else:
				for counter in range(4):
					# SETS ALL OBJ PROPERTIES FOR TIER 0-3 AND RATES 0-3
					gridlabd.set_value(tariff_name, types[type_idx]+"_rate"+str(counter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"rate"]))
					gridlabd.set_value(tariff_name, types[type_idx]+"_tier"+str(counter), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter)+"max"]))

				# SETS ALL OBJ PROPERTY FOR RATE 4
				gridlabd.set_value(tariff_name, types[type_idx]+"_rate"+str(counter+1), str(tariff_data.at[0,"energyratestructure/period"+str(pcounter)+"/tier"+str(counter+1)+"rate"]))

				pcounter = 0
				type_idx = type_idx + 1

	return rates, schedule

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
		
		# gets .gz file from OpenEi database
		with open(filename, "wb") as f:
			r = requests.get(url)
			f.write(r.content) 
		fgzip = gzip.open(filename,'rb')

		# unzips .gz file    
		with gzip.open(filename, 'r') as f_in, open('usurdb.csv', 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)

	# IS THIS CORRECT TO SET DELTA TO 1 HR
	meter = gridlabd.get_object("test_meter")
	delta = to_float(gridlabd.get_value(meter["name"],"measured_energy_delta_timestep"))
	if delta != 3600:
		print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
		gridlabd.setvalue(meter["measured_energy_delta_timestep"],"measured_energy_delta_timestep", str(3600))

	t_counter = int(input("Enter desired tariff index from tariff_libray_csv. (Note csv is 0 indexed):"))
	
	global tariff_df # reads tariff on init 
	tariff_df = read_tariff("tariff_library_config.csv", t_counter) # Could edit to allow user to input csv path?

	return True

def on_commit(t):

	# TEST THIS CODE
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')	
	seconds = (clock.hour * 60 + clock.minute) * 60 + clock.second
	hour = clock.hour

	if seconds % 3600 == 0: # can add error flag if it skips an hour just assume it works
		print(clock)

		bill = gridlabd.get_object("test_bill")
		bill_name = bill["name"]
		meter = gridlabd.get_object("test_meter")
		meter_name = meter["name"]
		tariff = gridlabd.get_object("tariff")
		tariff_name = tariff["name"]

		# 7/19 TESTING MOVING THIS CODE TO ON_INIT TO SPEED UP RUN TIME
		#path = "tariff_library_config.csv" #EDIT TO ALLOW USER TO CHANGE
		#t_counter = 0 #EDIT TO ALLOW USER TO CHANGE
		#tariff_df = read_tariff(path, t_counter)

		# get previous daily energy usage
		previous_usage = to_float(gridlabd.get_value(bill_name, 'usage'))

		# get previous billing_days
		billing_days = to_float(gridlabd.get_value(bill_name, "billing_days"))

		# energy usage over the hour
		energy_hr =(to_float(gridlabd.get_value(meter_name, 'measured_real_energy_delta')))/1000 #kWh

		# CHECK IF THIS CODE WORKS
		# check if in same day/ if timing needs to be updated
		day = clock.day
		global rates
		global schedule
		global tariff_df
		if billing_days == 0.0:
			rates, schedule = monthlyschedule_gen(tariff_df)
		elif day != previous_day:
			rates, schedule = monthlyschedule_gen(tariff_df)
		previous_day = day

		# check if if time is peak/shoulder/offpeak
		print(schedule,hour) # for testing fatal error
		type_idx = rates.index(schedule[hour])

		if len(rates) == 3:
			if type_idx == 0:
				string = "offpeak"
			elif type_idx == 1:
				string = "shoulder"
			else:
				string = "peak"
		else:
			if type_idx == 0:
				string = "offpeak"
			else:
				string ="peak"   

		global RATE_FLAG

		if RATE_FLAG == "True":
			daily_usage = previous_usage + energy_hr


			tier=[0,0,0,0]
			rate=[0,0,0,0,0]

			for counter in range(4):
					tier[counter] = to_float(gridlabd.get_value(tariff_name, string+'_tier'+str(counter)))
					rate[counter] = to_float(gridlabd.get_value(tariff_name, string+'_rate'+str(counter)))

			rate[counter+1] = to_float(gridlabd.get_value(tariff_name, string+'_rate'+str(counter+1)))
			
			# THIS IS FAILING 
			tier0 = max(min(daily_usage, tier[0]) - previous_usage, 0) 
			tier1 = max(min(daily_usage, tier[1]) - previous_usage - tier0, 0, energy_hr-tier0)
			tier2 = max(min(daily_usage, tier[2]) - previous_usage - tier0 - tier1, 0, energy_hr-tier0-tier1)
			tier3 = max(min(daily_usage, tier[3]) - previous_usage - tier0 - tier1 - tier2, 0, energy_hr-tier0-tier1-tier2)
			tier4 = max(energy_hr - tier0 - tier1 - tier2 - tier3, 0)

			hr_charge = rate[0]*tier0+rate[1]*tier1+rate[2]*tier2+rate[3]*tier3+rate[4]*tier4
			gridlabd.set_value(bill_name,"total_charges",str(to_float(bill["total_charges"])+hr_charge))
			
			if day != previous_day:
				gridlabd.set_value(bill_name, "usage", str(0.0))
			else:
				gridlabd.set_value(bill_name, "usage", str(daily_usage))

			gridlabd.set_value(bill_name,"billing_days",str(billing_days+1/24))

			# ADDED TO SEE RESULTS
			print("KWh:", energy_hr," Total charges:", gridlabd.get_value(bill_name,"total_charges"),"Hr charges", hr_charge, " Daily usage:" , daily_usage)
			print(rate[0],rate[1],rate[2],rate[3],rate[4])
			print(tier0,tier1,tier2,tier3,tier4, "\n")
		
		else:
			print("Implementation for non-inclining block rate in progress") 

	else:
		# Removing this print out for clarity
		d=0
		#print("Time passed was not a complete hour. Billing unchanged")

	return gridlabd.NEVER