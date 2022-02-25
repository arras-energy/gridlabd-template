import os
import gridlabd
import csv
import pandas 
import datetime
from dateutil import parser
import re
import sys

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
		idx = gridlabd.get_global("TARIFF_INDEX_SPECIFIC") # multiple tariffs match, so get specific one
		if (idx == None or int(idx) >= df.shape[0]):
			for i in range(df.shape[0]):
				print("Index",i,": ", df.iloc[i,3]) # print df name
			raise ValueError("Please provide row TARIFF_INDEX_SPECIFIC with corresponding int value from a choice above in config.csv.")
		idx = int(idx)
		tariff_data = pandas.DataFrame(data=df.iloc[[idx]]).reset_index(drop=True)
		# This is currently rasiing errors in docker?
	elif df.shape[0] == 0:
		raise ValueError("No active tariff found in OpenEi database matching information. Simulation ending") 
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

	# splits schedule into a list
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

	# fills in tariff obj with peak and offpeak rates
	if len(rates) > 3:
		raise Exception("Implementation for > 3 TOU rates per day in progress") 
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

	# Sets delta to 1 hr
	meter = gridlabd.get_object("test_meter")
	delta = to_float(gridlabd.get_value(meter["name"],"measured_energy_delta_timestep"))
	if delta != 3600:
		print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
		gridlabd.setvalue(meter["measured_energy_delta_timestep"],"measured_energy_delta_timestep", str(3600))

	t_counter = int(gridlabd.get_global("tariff_index"))
	# removed to get rid of terminal input
	#t_counter = int(input("Enter desired tariff index from tariff_library_config.csv (Note csv is 0 indexed):"))
	
	global tariff_df # reads tariff on init 
	
	try:
		tariff_df = read_tariff("tariff_library_config.csv", t_counter) # Could edit to allow user to input csv path?
	except ValueError as e:
		print(e)
		sys.exit(1) 

	return True

def on_commit(t):

	# TEST THIS CODE
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')	
	seconds = (clock.hour * 60 + clock.minute) * 60 + clock.second
	hour = clock.hour

	if seconds % 3600 == 0: # can add error flag if it skips an hour just assume it works

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

		# get previous billing_hrs
		billing_hrs = to_float(gridlabd.get_value(bill_name, "billing_hrs"))

		# energy usage over the hour
		energy_hr =(to_float(gridlabd.get_value(meter_name, 'measured_real_energy_delta')))/1000 #kWh

		# check if in same day/ if timing needs to be updated
		day = clock.day
		global rates
		global schedule
		global tariff_df
		global previous_day
		if billing_hrs == 0.0:
			rates, schedule = monthlyschedule_gen(tariff_df)
			previous_day = day
		elif day != previous_day:
			rates, schedule = monthlyschedule_gen(tariff_df)
			gridlabd.set_value(bill_name, "usage", str(0.0))
		
		previous_day = day

		# get previous daily energy usage
		previous_usage = to_float(gridlabd.get_value(bill_name, 'usage'))

		# check if if time is peak/shoulder/offpeak
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
			
			# Fixed?
			if tier[0] != 0.0:
				tier0 = max(min(daily_usage, tier[0]) - previous_usage, 0) 
			else:
				tier0 = energy_hr
			if tier[1] != 0.0:
				tier1 = max(min(daily_usage, tier[1]) - previous_usage - tier0, 0)
			else:
				tier1 = max(min(daily_usage, tier[1]) - previous_usage - tier0, 0, energy_hr-tier0)
			if tier[2] != 0.0:
				tier2 = max(min(daily_usage, tier[2]) - previous_usage - tier0 - tier1, 0)
			else:
				tier2 = max(min(daily_usage, tier[2]) - previous_usage - tier0 - tier1, 0, energy_hr-tier0-tier1)
			if tier[3] != 0.0:
				tier3 = max(min(daily_usage, tier[3]) - previous_usage - tier0 - tier1 - tier2, 0)
			else:
				tier3 = max(min(daily_usage, tier[3]) - previous_usage - tier0 - tier1 - tier2, 0, energy_hr-tier0-tier1-tier2)
			
			tier4 = max(energy_hr - tier0 - tier1 - tier2 - tier3, 0)

			hr_charge = rate[0]*tier0+rate[1]*tier1+rate[2]*tier2+rate[3]*tier3+rate[4]*tier4

			gridlabd.set_value(bill_name,"total_charges",str(to_float(bill["total_charges"])+hr_charge))
			gridlabd.set_value(bill_name,"billing_hrs",str(billing_hrs + 1))
			gridlabd.set_value(bill_name, "usage", str(daily_usage))
			gridlabd.set_value(bill_name, "total_usage", str(energy_hr + to_float(gridlabd.get_value(bill_name, "total_usage"))))

			triplex_meter = gridlabd.get_object("test_meter")
			meter_name = triplex_meter["name"]
			gridlabd.set_value(bill_name, "total_power", str(to_float(gridlabd.get_value(meter_name, "measured_real_power")) + to_float(gridlabd.get_value(bill_name, "total_power"))))

			# Add if verbose is on print this?
			#print(clock)
			#print("KWh:", energy_hr," Total charges:", gridlabd.get_value(bill_name,"total_charges"),"Hr charges", hr_charge, " Daily usage:" , daily_usage, "Total usage:", gridlabd.get_value(bill_name,"total_usage"))
			#print()


		else:
			print("Implementation for non-inclining block rate in progress") 
	else:
		d=0
		# Add here if verbose is on print this?
		#print("Time passed was not a complete hour. Billing unchanged")

	return gridlabd.NEVER

def on_term(t):
	bill = gridlabd.get_object("test_bill")
	bill_name = bill["name"]
	triplex_meter = gridlabd.get_object("test_meter")
	meter_name = triplex_meter["name"]
	# Search for floating point 
	# total_charges = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_charges")))
	# total_usage = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_usage")))
	# billing_hrs = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"billing_hrs")))
	# total_power = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_power")))
	total_charges_split = str(gridlabd.get_value(bill_name,"total_charges")).split(" ")
	total_usage_split = str(gridlabd.get_value(bill_name,"total_usage")).split(" ")
	billing_hrs = str(gridlabd.get_value(bill_name,"billing_hrs")) # no split because get_value does not return a unit
	total_power_split = str(gridlabd.get_value(bill_name,"total_power")).split(" ")



	print("Total charges:", gridlabd.get_value(bill_name,"total_charges"), "Total usage:", gridlabd.get_value(bill_name,"total_usage"), "Total hrs:", gridlabd.get_value(bill_name,"billing_hrs"), "Total power:", gridlabd.get_value(bill_name,"total_power"))
	# Removes + sign at the beginning of string
	df = pandas.DataFrame([[total_charges_split[0][1:], total_charges_split[1]], [total_usage_split[0][1:], total_usage_split[1]], [billing_hrs[1:], "hrs"], [total_power_split[0][1:], total_power_split[1]]], ["Total Charges", "Total Usage", "Total Duration", "Total Power"],["Value", "Units"])
	print(df)
	df.to_csv('output.csv')


	# Add writing to own csv here?
	# Could use on exit in terminal and look at json file maybe?
	return None
