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

def read_tariff(idx):
	pandas.set_option("max_rows",None)
	pandas.set_option("max_columns",None)
	data = pandas.read_csv("pge_residentialtariffs.csv",low_memory=False)

	tariff_data = pandas.DataFrame(data.iloc[idx]).transpose().reset_index(drop=True)

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

	# IS THIS CORRECT TO SET DELTA TO 1 HR
	meter = gridlabd.get_object("test_meter")
	delta = to_float(gridlabd.get_value(meter["name"],"measured_energy_delta_timestep"))
	if delta != 3600:
		print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
		gridlabd.setvalue(meter["measured_energy_delta_timestep"],"measured_energy_delta_timestep", str(3600))

	t_counter = int(input("Enter desired tariff index from tariff_library_config.csv (Note csv is 0 indexed):"))
	
	global tariff_df # reads tariff on init 
	tariff_df = read_tariff(t_counter) # Could edit to allow user to input csv path?

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

		# get previous billing_hrs
		billing_hrs = to_float(gridlabd.get_value(bill_name, "billing_hrs"))

		# energy usage over the hour
		energy_hr =(to_float(gridlabd.get_value(meter_name, 'measured_real_energy_delta')))/1000 #kWh

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
		RATE_FLAG = "True"

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

			# ADDED TO SEE RESULTS
			#print(clock)
			#print("KWh:", energy_hr," Total charges:", gridlabd.get_value(bill_name,"total_charges"),"Hr charges", hr_charge, " Daily usage:" , daily_usage, "Total usage:", gridlabd.get_value(bill_name,"total_usage"))
			#print()

			# Removing this print for less clutter
			#print(rate[0],rate[1],rate[2],rate[3],rate[4], tier[0],tier[1],tier[2],tier[3])
			#print(tier0,tier1,tier2,tier3,tier4, "\n")

		else:
			print("Implementation for non-inclining block rate in progress") 
	else:
		# Removing this print out for clarity
		d=0

	return gridlabd.NEVER

def on_term(t):
	bill = gridlabd.get_object("test_bill")
	bill_name = bill["name"]
	
	csvname = "output_pge_residential.csv"

	file_exists = os.path.isfile(csvname)
	with open(csvname, mode='a',newline='') as file:
		file_writer = csv.writer(file,delimiter =",")

		if not file_exists:
			file_writer.writerow(['name','total charges ($)','total energy (kWh)','total time (hrs)'])

		file_writer.writerow([tariff_df.iloc[0,3],to_float(gridlabd.get_value(bill_name,"total_charges")),to_float(gridlabd.get_value(bill_name,"total_usage")),to_float(gridlabd.get_value(bill_name,"billing_hrs"))])
	
	print()
	return None