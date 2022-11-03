import os
import gridlabd
import csv
import pandas 
import datetime
from datetime import date
from dateutil import parser
import re
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.ticker as ticker
import numpy as np
import logging
from calendar import monthrange

#
# Local data model
#

data_model = {}

def get_value(obj,prop):
	global data_model
	return str(data_model[obj][prop])

def set_value(obj,prop,value):
	global data_model
	old = data_model[obj][prop]
	data_model[obj][prop]=value
	return old

#
# Analysis
#

meter_name_list = None

def to_float(x):
	return float(x.split(' ')[0])

def to_datetime(x,format):
	return parser.parse(x)

def round_decimals(value):
	NO_OF_DIGITS = 1
	return round(value, NO_OF_DIGITS)

def read_tariff(pathtocsv, tariff_counter):

	__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	# reads USA tariff csv usurdb.csv from OpenEi
	pandas.options.display.max_rows = None
	pandas.options.display.max_rows = None
	data = pandas.read_csv("usurdb.csv",low_memory=False)

	# read in csv file depending on tariff counter value
	with open(os.path.join(__location__, pathtocsv)) as fp:
		reader = csv.reader(fp, skipinitialspace=True, delimiter=",")
		next(reader)
		tariff_input = [row for row in reader]

	# get inputs from csv (TARIFF_INDEX in config.csv determines the tariff to run)
	# TO DO: change this so all the tariff are run from file and compared 
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

	tariff_data.to_csv("tariff_data.csv",header=True,index=True)

	return tariff_data # returns df of associated tariff

def monthlyschedule_gen(tariff_data, clock): #Inputs tariff df from csv and populates tariff gridlabd obj

	# Finding default tariff obj name from gridlabd	
	tariff = gridlabd.get_object("tariff")
	tariff_name = tariff["name"]

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
	#global rates
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


def update_bill_values(bill, meter_name, prev_day,clock): 
	""" 
	Updates the bill values of the specific meter_name. Uses clock and previous day to reset usage in the bill. 
	This function is called every hour for each meter and triplex meter. 
	"""
	hour = clock.hour
	tariff_name = "tariff" # tariff["name"]
	bill_name = bill["name"]
	meter = gridlabd.get_object(meter_name)
	# billing_hrs = to_float(gridlabd.get_value(bill_name, "billing_hrs"))

	billing_hrs = float(get_value(bill_name,"billing_hrs"))
	# energy usage over the hour
	# energy_hr = (to_float(gridlabd.get_value(meter_name, 'measured_real_energy_delta')))/1000 #kWh
	energy_hr = gridlabd.get_double(gridlabd.get_property(meter_name,"measured_real_energy_delta"))/1000.0
	# print('test_2')
	# check if in same day/ if timing needs to be updated
	day = clock.day

	global rates
	global schedule
	global data_model
	
	# usage_addr = gridlabd.get_property(bill_name,"usage")
	if billing_hrs == 0.0:
		rates, schedule = monthlyschedule_gen(tariff_df, clock)
		previous_usage = float(get_value(bill_name,"usage"))
	elif day != prev_day:
		rates, schedule = monthlyschedule_gen(tariff_df, clock)
		# gridlabd.set_value(bill_name, "usage", str(0.0))
		previous_usage = 0.0
	else:		
	
		# get previous daily energy usage
		# previous_usage = to_float(gridlabd.get_value(bill_name, 'usage'))
		previous_usage = float(get_value(bill_name,"usage"))

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
		# Calculate charge for this hour
		daily_usage = previous_usage + energy_hr

		tier=[0,0,0,0]
		rate=[0,0,0,0,0]

		for counter in range(4):
				tier[counter] = to_float(gridlabd.get_value(tariff_name, string+'_tier'+str(counter)))
				rate[counter] = to_float(gridlabd.get_value(tariff_name, string+'_rate'+str(counter)))

		rate[counter+1] = to_float(gridlabd.get_value(tariff_name, string+'_rate'+str(counter+1)))
		
		
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

		# update bill values of this meter with appropriate values. 
		gridlabd.set_value(bill_name,"total_charges",str(to_float(bill["total_charges"])+hr_charge))
		set_value(bill_name,"billing_hrs",str(billing_hrs + 1))
		# gridlabd.set_value(bill_name, "usage", str(daily_usage))
		set_value(bill_name,"usage",daily_usage)
		set_value(bill_name, "total_usage", str(energy_hr + to_float(get_value(bill_name, "total_usage"))))
		set_value(bill_name, "total_power", str(to_float(gridlabd.get_value(meter_name, "measured_real_power")) + to_float(get_value(bill_name, "total_power"))))
		#gridlabd.set_value(bill_name, "peak_power", str(max(to_float(gridlabd.get_value(meter_name, "measured_real_power")), to_float(gridlabd.get_value(bill_name, "peak_power")))))

def update_monthly_cumulative_meter_results(total_charges, total_usage, total_power, meter_name):
	# updates monthly cumulative results of meter
	set_value(meter_name, "monthly_updated_charges", str(total_charges))
	set_value(meter_name, "monthly_updated_usage", str(total_usage)) 
	set_value(meter_name, "monthly_updated_power", str(total_power)) 


def update_meter_results(charges_current_month,usage_current_month,power_current_month, demand_current_month, meter_name, month):
	print(f"update_meter_results <-- '{charges_current_month,usage_current_month,power_current_month, demand_current_month}'")
	global data_model
	# updates the string representation of a list of results
	set_value(meter_name, "monthly_charges",  f"{get_value(meter_name, 'monthly_charges')},{charges_current_month}")
	set_value(meter_name, "monthly_usage",  f"{get_value(meter_name, 'monthly_usage')},{usage_current_month}")
	set_value(meter_name, "monthly_power", f"{get_value(meter_name, 'monthly_power')},{power_current_month}")
	set_value(meter_name, "monthly_demand", f"{get_value(meter_name, 'monthly_demand')},{demand_current_month}")
	print(data_model)
	print(f"Month {month} done")


def update_meter_and_bill(meter_name, month):
	bill = gridlabd.get_object("bill_" + meter_name) # might not have bill object
	bill_name = bill["name"]

	total_charges = to_float(gridlabd.get_value(bill_name,"total_charges"))
	total_usage = to_float(get_value(bill_name,"total_usage"))
	total_power = to_float(get_value(bill_name,"total_power"))
	logging.debug(f"total_charges = {total_charges}")

	charges_current_month = total_charges - to_float(get_value(meter_name, "monthly_updated_charges"))
	usage_current_month = total_usage - to_float(get_value(meter_name, "monthly_updated_usage"))
	power_current_month = total_power - to_float(get_value(meter_name, "monthly_updated_power"))
	logging.debug(f"total_charges_current month = {charges_current_month}")

	# measured_demand = gridlabd.get_property(meter_name,"measured_demand")
	# demand_current_month = gridlabd.get_double(measured_demand) #to_float(gridlabd.get_value(meter_name, "measured_demand"))
	demand_current_month = to_float(gridlabd.get_value(meter_name, "measured_demand"))
	print("DEMAND: " + str(demand_current_month))
	gridlabd.set_value(meter_name, "measured_demand", str(0.0))
	

	update_monthly_cumulative_meter_results(total_charges, total_usage,total_power,meter_name)
	update_meter_results(charges_current_month, usage_current_month, power_current_month, demand_current_month, meter_name, month)







def update_meter_timestep(meter_name, timestep):
	# sets the time step of meter to timestep 
	delta = to_float(gridlabd.get_value(meter_name,"measured_energy_delta_timestep"))
	if delta != timestep:
		print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
		gridlabd.set_value(meter_name,"measured_energy_delta_timestep", str(timestep))

# Another option to determine number of bins: 
# Title: Determining Histogram Bin Width using the Freedman-Diaconis Rule
# Author: James D. Triveri 
# Date: 03-02-2019
# Availability: http://www.jtrive.com/determining-histogram-bin-width-using-the-freedman-diaconis-rule.html
def freedman_diaconis_width(data):
    """
    Use Freedman Diaconis rule to compute optimal histogram bin width. 
    ``returnas`` can be one of "width" or "bins", indicating whether
    the bin width or number of bins should be returned respectively. 


    Parameters
    ----------
    data: np.ndarray
        One-dimensional array.

    returnas: {"width", "bins"}
        If "width", return the estimated width for each histogram bin. 
        If "bins", return the number of bins suggested by rule.
    """
    data = np.asarray(data, dtype=np.float_)
    IQR  = stats.iqr(data, rng=(25, 75), scale=1.0, nan_policy="raise")
    N    = data.size
    bw   = (2 * IQR) / np.power(N, 1/3)
    datmin, datmax = data.min(), data.max()
    datrng = datmax - datmin
    if IQR==0:
    	result = 1 # Handles corner case of no spread for IQR. In that case, return 1 bin.
    else:
    	result = int((datrng / bw) + 1)
    return(result)

# Currently used to determine number of bins. 
def sturg_rule_number_of_bins(data):
	return int(1 + round((3.322 * np.log10(len(data)))))

def generate_results_date_and_days(year, month, day, hour, delta_days):
	result_dates = []
	days = []
	number_of_months = (year - start_year) * 12 + (month - start_month) + 1  # the 1 because we want to count current month as well
	days.append(f"{delta_days}") # first row is total 
	
	if number_of_months > 1: 
		# Only append if simulation does not end in same month
		days.append(f"{round_decimals(monthrange(start_year,start_month)[1] - start_day - (start_hour/24.0) + 1 )}") # start day to end of month 
		result_dates.append(f"{start_year}-{start_month}-{monthrange(start_year,start_month)[1]}") # this list is for plotting graph since the graph does not want a total
	for num_month in range(1,number_of_months - 1):
		# calculate dates and number of days for the in between months 
		curr_year = int(start_year + (num_month + start_month)/13)
		curr_month = (num_month + start_month - 1) % 12 + 1
		curr_day = monthrange(curr_year,curr_month)[1]
		result_dates.append(f"{curr_year}-{curr_month}-{curr_day}")
		days.append(curr_day)
	result_dates.append(f"{year}-{month}-{day}") # last date is current simulation date
	if number_of_months > 1:
		days.append(f"{round_decimals(day - 1 + (hour/24.0))}") # last number of days is current day of simulation 
	else:
		days.append(f"{round_decimals(day - start_day + (hour - start_hour)/24)}")
	return result_dates, days

def update_monthly_demand_triplex(triplex_meter_name):
	# Updates triplex bill with the max of the current peak power vaule and the current month measured demand generated from the triplex meter. 
	# Resets measured demand of triplex meter.
	bill_name = gridlabd.get_object("bill_" + triplex_meter_name)["name"]
	greater = max(to_float(get_value(bill_name, "peak_power")), to_float(gridlabd.get_value(triplex_meter_name, "measured_demand")))
	set_value(bill_name, "peak_power", str(greater))
	gridlabd.set_value(triplex_meter_name, "measured_demand", str(0.0))


def on_init(t):

	# set up logging
	# logging.basicConfig(level=logging.DEBUG)
	# logger = logging.getLogger()
	# logger.disabled = True

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

	t_counter = int(gridlabd.get_global("TARIFF_INDEX"))

	global tariff_df 
	try:
		tariff_df = read_tariff("tariff_library_config.csv", t_counter) # Could edit to allow user to input csv path?
	except ValueError as e:
		gridlabd.error(str(e))
		sys.exit(1) 


	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')

	# Set up the needed globals 
	global start_year # For calculation of date column for meters 
	start_year = clock.year

	global start_month # For calculation of date column for meters 
	start_month = clock.month

	global start_day # For calculation of date column for meters
	start_day = clock.day

	global start_hour # For calculation of date column for meters
	start_hour = clock.hour 
	
	global prev_month # For determining when simulation has moved on to a new month
	prev_month = clock.month

	global prev_day # For determining when simulation has moved on to a new day 
	prev_day = clock.day

	global triplex_name_list # The names of all triplex meters
	global meter_name_list # The names of all meters
	obj_list = gridlabd.get("objects")
	triplex_name_list = [] 
	meter_name_list = [] 
	for obj in obj_list:	
		data = gridlabd.get_object(obj)
		if data["class"] == "triplex_meter":
			triplex_name_list.append(obj) # appends the name of the triplex meter rather than the actual object 
			update_meter_timestep(obj, 3600) # meter time step to be an hour 
			data_model["bill_"+obj]={"total_power" : "0.0", "total_usage" : "0.0", "billing_hrs" : "0.0", "usage" : "0.0", "peak_power" : "0.0"}
		if data["class"] == "meter":
			meter_name_list.append(obj)
			# initialize values 
			update_meter_timestep(obj, 3600)
			data_model[obj] = {"monthly_charges" : "0.0", "monthly_usage" : "0.0", "monthly_power" : "0.0", "monthly_demand" : "0.0", "monthly_updated_charges" : "0.0", "monthly_updated_usage" : "0.0", "monthly_updated_power" : "0.0"}
			data_model["bill_"+obj]={"total_power" : "0.0", "total_usage" : "0.0", "billing_hrs" : "0.0", "usage" : "0.0", "peak_power" : "0.0"}
	print(data_model)
	return True



def on_commit(t):
	# Update all meters and triplex meters each hour. Also updates monthly values for meters every new month.
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	hour = clock.hour
	seconds = (clock.hour * 60 + clock.minute) * 60 + clock.second
	if seconds % 3600 == 0: 
		global prev_month	
		year = clock.year 
		month = clock.month
		day = clock.day
		if prev_month != month:
			for index, meter_name in enumerate(meter_name_list):
				# update meter and meter bill values 
				update_meter_and_bill(meter_name, prev_month-1)
			for triplex_meter_name in triplex_name_list:
				update_monthly_demand_triplex(triplex_meter_name)
			# update measured demand for month for triplex meters
				
			prev_month = month
		global prev_day

		for meter_name in meter_name_list:
			# update bill values for each meter

			meter_bill = gridlabd.get_object("bill_" + meter_name)
			update_bill_values(meter_bill, meter_name, prev_day,clock)

		for triplex_meter_name in triplex_name_list:
			# updates bill values of each triplex meter
			triplex_bill = gridlabd.get_object("bill_" + triplex_meter_name)
			# print("month: " + str(month))
			update_bill_values(triplex_bill,triplex_meter_name, prev_day,clock)
		prev_day = day 


	return gridlabd.NEVER

def plot_meter_graph(X, Y, y_label, title, result_name):
	# Outputs 3 png, each with 1 graph (charges, usage, power) for a certain meter. Uses the properties monthly_charges, monthly_usage, monthly_power 
	fig = plt.figure()
	fig.set_size_inches(15, 8)
	plt.clf()
	ax = fig.add_axes([0,0,1,1])
	ax.bar(X,Y)
	plt.xlabel('Months')
	plt.ylabel(y_label)
	plt.title(title)
	# pdf.savefig(bbox_inches="tight", dpi=150)
	plt.savefig(result_name, bbox_inches='tight', dpi=150)
	#pdf = PdfPages("results_" + str(meter_name) + ".pdf")
	#pages = convert_from_path("results_" + str(meter_name) + ".pdf", 500)
	#page.save("results_" + str(meter_name) + ".png", 'PNG')
	#pdf.close()

def plot_triplex_meter_histograms(X, x_label, title, result_name):
	# Outputs histogram for distribution of all triplex meters for charges, usage, and power. 
	
	fig = plt.figure()
	plt.clf()
	NBR_BINS = sturg_rule_number_of_bins(X)
	ax = fig.add_axes([0,0,1,1])
	for axis in [ax.xaxis, ax.yaxis]:
		axis.set_major_locator(ticker.MaxNLocator(integer=True))
	ax.hist(X, bins = NBR_BINS, edgecolor = "black")
	plt.xlabel(x_label)
	plt.ylabel('Number of Triplex Meters')
	plt.title(title)
	plt.savefig(result_name, bbox_inches='tight', dpi=150)
		#pdf.savefig(bbox_inches="tight", dpi=150)
	#pdf = PdfPages("triplex_results" + ".pdf")
	#pages = convert_from_path("triplex_results" + ".pdf", 500)
	#page.save('triplex_results.png', 'PNG')
	#pdf.close()

def on_term(t):
	global prev_month
	global data_model
	print(data_model)
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	year = clock.year 
	month = clock.month
	day = clock.day
	hour = clock.hour
	for index, meter_name in enumerate(meter_name_list):
		# updates each meter for the current month (when simulation ends in middle of month)
		update_meter_and_bill(meter_name, month-1)
	for triplex_meter_name in triplex_name_list:
		update_monthly_demand_triplex(triplex_meter_name)


	# get results for all meters for output.csv 
	charges_meter_list, usage_meter_list, total_power_meter_list, months_meter_list, measured_demand_meter_list = ([] for i in range(5))

	
	for meter_name in meter_name_list:

		# temp list for graphing without a total for graphing. List with total is for output.csv 
		current_meter_monthly_charges = [round_decimals(float(val)) for val in get_value(meter_name, "monthly_charges").split(",")][1:] # first element of list is zero 
		charges_meter_list.append(round_decimals(to_float(gridlabd.get_value("bill_" + meter_name,"total_charges"))))
		charges_meter_list.extend(current_meter_monthly_charges) 

		current_meter_monthly_usage = [round_decimals(float(val)) for val in get_value(meter_name, "monthly_usage").split(",")][1:]
		usage_meter_list.append(round_decimals(to_float(get_value("bill_" + meter_name,"total_usage"))))
		usage_meter_list.extend(current_meter_monthly_usage)

		current_meter_monthly_power = [round_decimals(float(val)) for val in get_value(meter_name, "monthly_power").split(",")][1:]
		total_power_meter_list.append(round_decimals(to_float(get_value("bill_" + meter_name,"total_power"))))
		total_power_meter_list.extend(current_meter_monthly_power)

		current_meter_monthly_demand = [round_decimals(float(val)) for val in get_value(meter_name, "monthly_demand").split(",")][1:]
		measured_demand_meter_list.append(max(current_meter_monthly_demand)) # gets the max of all the monthly demand 
		measured_demand_meter_list.extend(current_meter_monthly_demand)

		months_meter_list.append(f"{year}-{month}-{day}") # first row is total so date of end of simulation 
		delta_days = round_decimals((date(year, month, day) - date(start_year, start_month, start_day)).days + (hour/24.0) - (start_hour/24.0))

		# generates the dates of results and number of days in the results
		result_dates, days = generate_results_date_and_days(year, month, day, hour, delta_days)



		plot_meter_graph(result_dates, current_meter_monthly_charges, "Charges ($)", f"{meter_name} Monthly Charges", f"{meter_name}_month_charges.png")
		plot_meter_graph(result_dates, current_meter_monthly_usage, "Usage (kWh)", f"{meter_name} Monthly Usage", f"{meter_name}_month_usage.png")
		plot_meter_graph(result_dates, current_meter_monthly_power, "Power (W)", f"{meter_name} Monthly Power", f"{meter_name}_month_power.png")
		plot_meter_graph(result_dates, current_meter_monthly_demand, "Demand (W)", f"{meter_name} Monthly Demand", f"{meter_name}_month_demand.png")

		months_meter_list.extend(result_dates) 

	# get results for all triplex meters 
	charges_triplex_meter_list = [round_decimals(to_float(gridlabd.get_value("bill_" + triplex_name,"total_charges"))) for triplex_name in triplex_name_list]
	usage_triplex_meter_list = [round_decimals(to_float(get_value("bill_" + triplex_name,"total_usage"))) for triplex_name in triplex_name_list]
	peak_power_triplex_meter_list = [round_decimals(to_float(get_value("bill_" + triplex_name,"peak_power"))) for triplex_name in triplex_name_list]
	total_power_triplex_meter_list = [round_decimals(to_float(get_value("bill_" + triplex_name,"total_power"))) for triplex_name in triplex_name_list]



	meter_name_dupe_list = [val for val in meter_name_list for i in get_value(meter_name, "monthly_charges").split(",")] # duplicate meter name for each month value 

	plot_triplex_meter_histograms(charges_triplex_meter_list, "Charges ($)", "Distribution of Charges", "distribution_of_charges.png")
	plot_triplex_meter_histograms(usage_triplex_meter_list, "Usage (kWh)", "Distribution of Usage", "distribution_of_usage.png")
	plot_triplex_meter_histograms(peak_power_triplex_meter_list, "Peak Power (W)", "Distribution of Peak Power", "distribution_of_peak_power.png")


	# appends meter list and its results to triplex meter list and its results. Will add these as columns to .csv file 
	charges_meter_list.extend(charges_triplex_meter_list)
	usage_meter_list.extend(usage_triplex_meter_list)
	measured_demand_meter_list.extend(peak_power_triplex_meter_list)
	meter_name_dupe_list.extend(triplex_name_list)
	total_power_meter_list.extend(total_power_triplex_meter_list)

	for meter_name in triplex_name_list:
		# All triplex values are totals, not split by month
		months_meter_list.append(f"{year}-{month}-{day}") 
		days.append(delta_days)
	# add to dataframe by column 
	df = pandas.DataFrame({"Meter_ID": meter_name_dupe_list})
	df["Date"] = months_meter_list
	df["Days"] = days
	df["Cost ($)"] = charges_meter_list
	df["Energy (kWh)"] = usage_meter_list
	df["Peak Power (W)"] = measured_demand_meter_list
	df = df.set_index('Meter_ID')
	print(df)
	df.to_csv('output.csv')

	return None
