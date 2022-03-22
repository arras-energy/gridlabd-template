import os
import gridlabd
import csv
import pandas 
import datetime
from dateutil import parser
import re
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


#list comprehension for each element in the list. 
# Goal: We need to generate different types of graphs based on meters (big) and triplex meters (per house). Meters should generate bar graphs for charges, energy, peak power.
# Triplex meters should generate histograms for ranges of results for charges, energy, sum power?
# 1) Build upon what I already have: one meter to generate bar graphs. Change it to take all the meters in the model and generate bar graphs. 
# Keep track of demand (peak power) instead of total power. 
#	Populate a list in onInit filled with the different meters. Oncommit gets the values for each meter 
# a = [x["energy"] for x in list] 
# 2) Add support for triplex meters. on_term, get all their charges, energy, and sum of power (depending on time frame). Generate histogram based on those ranges. 
# can use numpy arrays
# global constants for indecies of meter_results_list 
CHARGES_INDEX = 0 
USAGE_INDEX = 1
POWER_INDEX = 2

def to_float(x):
	return float(x.split(' ')[0])

def to_datetime(x,format):
	return parser.parse(x)

def read_tariff(pathtocsv, tariff_counter):

	__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	# reads USA tariff csv usurdb.csv from OpenEi
	pandas.set_option("max_rows",None)
	pandas.set_option("max_columns",None)
	data = pandas.read_csv("usurdb.csv",low_memory=False)

	# read in csv file depending on tariff counter value
	with open(os.path.join(__location__, pathtocsv)) as fp:
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
			raise ValueError("Please provide row TARIFF_INDEX_SPECIFIC with corresponding int value from a choice in stdout.")
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


def update_bill_values(bill, meter, clock): 
	hour = clock.hour
	tariff = gridlabd.get_object("tariff")
	tariff_name = tariff["name"]
	bill_name = bill["name"]
	meter_name = meter["name"]

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

		triplex_meter = gridlabd.get_object("test_meter1")
		meter_name = triplex_meter["name"]
		gridlabd.set_value(bill_name, "total_power", str(to_float(gridlabd.get_value(meter_name, "measured_real_power")) + to_float(gridlabd.get_value(bill_name, "total_power"))))
		gridlabd.set_value(bill_name, "peak_power", str(max(to_float(gridlabd.get_value(meter_name, "measured_real_power")), to_float(gridlabd.get_value(bill_name, "peak_power")))))
		# Add if verbose is on print this?
		#print(clock)
		#print("KWh:", energy_hr," Total charges:", gridlabd.get_value(bill_name,"total_charges"),"Hr charges", hr_charge, " Daily usage:" , daily_usage, "Total usage:", gridlabd.get_value(bill_name,"total_usage"))
		#print()
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
	meter = gridlabd.get_object("test_meter1")
	delta = to_float(gridlabd.get_value(meter["name"],"measured_energy_delta_timestep"))
	if delta != 3600:
		print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
		gridlabd.setvalue(meter["measured_energy_delta_timestep"],"measured_energy_delta_timestep", str(3600))

	t_counter = int(gridlabd.get_global("tariff_index"))
	# removed to get rid of terminal input
	#t_counter = int(input("Enter desired tariff index from tariff_library_config.csv (Note csv is 0 indexed):"))
	
	global tariff_df # reads tariff on init 
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	# For graphing

	# Will hold a triple nested list. Inner most list contains 12 elements for the results of each month. Middle list holds 3 elements, 1 for each result type. Outer list
	# holds years of the element. Can get year by seeing how many elements in biggest list and subtract from end of simulation. 
	global meter_results_list 
	global prev_year
	global prev_month
	# Holds cumulative values. 
	global current_results_dict 
	# TODO: Have this dict for each meter in meter_list
	global triplex_meter_list
	global meter_list
	

	# TODO: make it global so other methods can refer to it 
	obj_list = gridlabd.get("objects")
	current_results_dict = {"charges" : 0, "usage" : 0, "power" : 0}
	triplex_meter_list = []
	meter_list = []
	for obj in obj_list:
		data = gridlabd.get_object(obj)
		if data["class"] == "triplex_meter":
			triplex_meter_list.append(data)
		if data["class"] == "meter":
			meter_list.append(data)
	#print(triplex_meter_list)
	#print(meter_list)


	# Don't need years anymore. So start with []. For each array in meter_list. Append [[]]. 
	meter_results_list = [[[0 for j in range (12)] for i in range(3)]]
	prev_year = clock.year
	prev_month = clock.month
	
	try:
		tariff_df = read_tariff("tariff_library_config.csv", t_counter) # Could edit to allow user to input csv path?
	except ValueError as e:
		gridlabd.error(str(e))
		sys.exit(1) 

	return True



def on_commit(t):
	# In array of meters, list comprehension and get the 3 results in another array. Get the sum. Put it into the meter_results_list for it.  

	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	seconds = (clock.hour * 60 + clock.minute) * 60 + clock.second
	hour = clock.hour
	year = clock.year 
	month = clock.month
	if seconds % 3600 == 0: # can add error flag if it skips an hour just assume it works
		# TODO: get bill object and meter for each in meters_list
		global prev_year
		global prev_month
		global current_results_dict
		# use histograph. for triplex meters. small number of homes, big ranges. large number , small ranges. how big should bins be? Not below $10. $25
		# ask gridlabd for objects of a particular class. 
		bill = gridlabd.get_object("bill_test_meter1")
		meter = gridlabd.get_object("test_meter1")
		


		if prev_month != month:
			
			# Update values for graphing when month changes 
			# total_charges_sum = [gridlabd.get_object(x)]
			total_charges = to_float(gridlabd.get_value(bill_name,"total_charges"))
			total_usage = to_float(gridlabd.get_value(bill_name,"total_usage"))
			total_power = to_float(gridlabd.get_value(bill_name,"total_power"))

			charges_current_month = total_charges - current_results_dict["charges"]
			usage_current_month = total_usage - current_results_dict["usage"]
			power_current_month = total_power - current_results_dict["power"]

			current_results_dict["charges"] = total_charges
			current_results_dict["usage"] = total_usage
			current_results_dict["power"] = total_power


			# print(charges_current_month)
			# print(usage_current_month)
			# print(hrs_current_month)
			# print(power_current_month)

			meter_results_list[-1][CHARGES_INDEX][prev_month-1] = charges_current_month
			meter_results_list[-1][USAGE_INDEX][prev_month-1] = usage_current_month
			meter_results_list[-1][POWER_INDEX][prev_month-1] = power_current_month
			
			prev_month = month
		for triplex_meter_obj in triplex_meter_list:
			triplex_bill = gridlabd.get_object("bill_" + triplex_meter_obj["name"])
			update_bill_values(triplex_bill,triplex_meter_obj,clock)
	else:
		d=0
		# Add here if verbose is on print this?
		#print("Time passed was not a complete hour. Billing unchanged")

	return gridlabd.NEVER

def plot_meter_graphs(current_year_results, current_year):
	# Outputs a pdf of 3 graphs (charges, usage, power) for a certain year. 

	def multiple_plot(X,Y, y_label):
		fig = plt.figure()
		fig.set_size_inches(15, 8)
		plt.clf()
		ax = fig.add_axes([0,0,1,1])
		ax.bar(X,Y)
		plt.xlabel('Months')
		plt.ylabel(y_label)
		plt.title(current_year)
		pdf.savefig(bbox_inches="tight", dpi=150)
	months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	results_charges = current_year_results[CHARGES_INDEX]
	results_usage = current_year_results[USAGE_INDEX]
	results_power = current_year_results[POWER_INDEX]
	pdf = PdfPages("results" + str(current_year) + ".pdf")
	multiple_plot(months, results_charges, "Charges ($)")
	multiple_plot(months, results_usage, "Usage (kWh)")
	multiple_plot(months, results_power, "Power (W)")
	pdf.close()
def plot_triplex_meter_histograms(charges_triplex_results_list, usage_triplex_results_list, peak_power_triplex_results_list):
	def multiple_plot_triplex(X, x_label):
		#figs, axs = plt.subplots(1,1, figsize=(10,7), tight_layout = True)
		fig = plt.figure()
		plt.clf()
		ax = fig.add_axes([0,0,1,1])
		ax.hist(X, bins = 5)
		plt.xlabel(x_label)
		plt.ylabel('Number of triplex meters')
		plt.title("Distribution of " + x_label + " of Triplex Meters")
		pdf.savefig(bbox_inches="tight", dpi=150)
	pdf = PdfPages("triplex_results" + ".pdf")
	multiple_plot_triplex(charges_triplex_results_list, "Charges ($)")
	multiple_plot_triplex(usage_triplex_results_list, "Usage (kWh)")
	multiple_plot_triplex(peak_power_triplex_results_list, "Power (W)")
	pdf.close()



def on_term(t):
	#remember to graph remaining of a month



	bill = gridlabd.get_object("bill_test_meter5")
	bill_name = bill["name"]
	triplex_meter = gridlabd.get_object("test_meter5")
	meter_name = triplex_meter["name"]

	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	year = clock.year 
	month = clock.month

	total_charges = to_float(gridlabd.get_value(bill_name,"total_charges"))
	total_usage = to_float(gridlabd.get_value(bill_name,"total_usage"))
	total_power = to_float(gridlabd.get_value(bill_name,"total_power"))

	charges_current_month = total_charges - current_results_dict["charges"]
	usage_current_month = total_usage - current_results_dict["usage"]
	power_current_month = total_power - current_results_dict["power"]

	current_results_dict["charges"] = total_charges
	current_results_dict["usage "] = total_usage
	current_results_dict["power"] = total_power


	# print(charges_current_month)
	# print(usage_current_month)
	# print(hrs_current_month)
	# print(power_current_month)

	meter_results_list[-1][CHARGES_INDEX][month-1] = charges_current_month
	meter_results_list[-1][USAGE_INDEX][month-1] = usage_current_month
	meter_results_list[-1][POWER_INDEX][month-1] = power_current_month


	for i in range(len(meter_results_list)):
		plot_meter_graphs(meter_results_list[i], year - (len(meter_results_list)-1) + i) # end year - (# of years in results list) = beginning year
	# Search for floating point 
	# total_charges = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_charges")))
	# total_usage = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_usage")))
	# billing_hrs = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"billing_hrs")))
	# total_power = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_power")))


	charges_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"total_charges")) for x in triplex_meter_list]

	usage_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"total_usage")) for x in triplex_meter_list]

	peak_power_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"peak_power")) for x in triplex_meter_list]

	print(charges_triplex_meter_list)
	plot_triplex_meter_histograms(charges_triplex_meter_list, usage_triplex_meter_list, peak_power_triplex_meter_list)


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
