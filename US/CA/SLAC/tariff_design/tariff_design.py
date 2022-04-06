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
import matplotlib.ticker as ticker
import numpy as np
from scipy import stats
import logging


# Try to put constraints on histogram to produce nicer looking histograms
# Put parents for the triplex_meter list and work out the code for that 
# Cite what i got from online
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


def update_bill_values(bill, meter, clock, prev_day): 
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
	
	if billing_hrs == 0.0:
		rates, schedule = monthlyschedule_gen(tariff_df)
	elif day != prev_day:
		rates, schedule = monthlyschedule_gen(tariff_df)
		gridlabd.set_value(bill_name, "usage", str(0.0))
	
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

		gridlabd.set_value(bill_name, "total_power", str(to_float(gridlabd.get_value(meter_name, "measured_real_power")) + to_float(gridlabd.get_value(bill_name, "total_power"))))
		gridlabd.set_value(bill_name, "peak_power", str(max(to_float(gridlabd.get_value(meter_name, "measured_real_power")), to_float(gridlabd.get_value(bill_name, "peak_power")))))
		print(bill_name + f" {hr_charge}" )
		# Add if verbose is on print this?
		#print(clock)
		#print("KWh:", energy_hr," Total charges:", gridlabd.get_value(bill_name,"total_charges"),"Hr charges", hr_charge, " Daily usage:" , daily_usage, "Total usage:", gridlabd.get_value(bill_name,"total_usage"))
		#print()
def update_monthly_results_dict_meter(total_charges, total_usage, total_power, index):
	monthly_results_dict_meter["charges"][index] = total_charges
	monthly_results_dict_meter["usage"][index] = total_usage
	monthly_results_dict_meter["power"][index] = total_power

def update_meter_results(charges_current_month,usage_current_month,power_current_month, meter_index, month):
	results_list_meter[meter_index][CHARGES_INDEX][month] = charges_current_month + results_list_meter[meter_index][CHARGES_INDEX][month]
	results_list_meter[meter_index][USAGE_INDEX][month] = usage_current_month + results_list_meter[meter_index][USAGE_INDEX][month]
	results_list_meter[meter_index][POWER_INDEX][month] = power_current_month + results_list_meter[meter_index][POWER_INDEX][month]


def update_meter_timestep(meter, timestep):
	delta = to_float(gridlabd.get_value(meter["name"],"measured_energy_delta_timestep"))
	if delta != timestep:
		print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
		gridlabd.set_value(meter["name"],"measured_energy_delta_timestep", str(timestep))

# Title: Determining Histogram Bin Width using the Freedman-Diaconis Rule
# Author: James D. Triveri 
# Date: 03-02-2019
# Availability: http://www.jtrive.com/determining-histogram-bin-width-using-the-freedman-diaconis-rule.html
def freedman_diaconis(data, returnas="width"):
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
    if returnas=="width":
        result = bw
    else:
        datmin, datmax = data.min(), data.max()
        datrng = datmax - datmin
        if IQR==0:
        	result = 1 # Handles corner case of no spread for IQR. In that case, return 1 bin.
        else:
        	result = int((datrng / bw) + 1)
    return(result)

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
	# meter = gridlabd.get_object("triplex_meter3")
	# delta = to_float(gridlabd.get_value(meter["name"],"measured_energy_delta_timestep"))
	# if delta != 3600:
	# 	print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
	# 	gridlabd.setvalue(meter["measured_energy_delta_timestep"],"measured_energy_delta_timestep", str(3600))

	t_counter = int(gridlabd.get_global("tariff_index"))

	#logging.basicConfig(level=logging.DEBUG)
	logger = logging.getLogger()
	logger.disabled = True
	# removed to get rid of terminal input
	#t_counter = int(input("Enter desired tariff index from tariff_library_config.csv (Note csv is 0 indexed):"))
	
	global tariff_df # reads tariff on init 
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	# For graphing

	# globals to keep track of meters and triplex meters along with their resutls
	global results_list_meter 
	global prev_year
	global prev_month
	global prev_day
	global monthly_results_dict_meter 
	global triplex_meter_list
	global meter_list
	
	prev_day = clock.day
	obj_list = gridlabd.get("objects")
	monthly_results_dict_meter = {"charges" : [], "usage" : [], "power" : []} # list contains charges/usage/power results of each meter
	triplex_meter_list = [] # list of triplex meter objects
	meter_list = [] # list of meter objects
	for obj in obj_list:
		data = gridlabd.get_object(obj)
		if data["class"] == "triplex_meter":
			triplex_meter_list.append(data)
			update_meter_timestep(data, 3600) # meter time step to be an hour 
		if data["class"] == "meter":
			meter_list.append(data)
			update_meter_timestep(data, 3600)
	#print(triplex_meter_list)
	#print(meter_list)


	results_list_meter = []
	for meter in meter_list:
		results_list_meter.append([[0 for j in range (12)] for i in range(3)]) # Outer list for each meter. Middle list for charges/usage/power. Inner list for months. For bargraph.
		monthly_results_dict_meter["charges"].append(0) # initialize to 0 for each meter. Helps keep track of monthly difference. I don't use bill because it updates every hour. 
		monthly_results_dict_meter["usage"].append(0)
		monthly_results_dict_meter["power"].append(0)
	print(monthly_results_dict_meter["charges"])
	prev_year = clock.year
	prev_month = clock.month
	
	try:
		tariff_df = read_tariff("tariff_library_config.csv", t_counter) # Could edit to allow user to input csv path?
	except ValueError as e:
		gridlabd.error(str(e))
		sys.exit(1) 

	return True



def on_commit(t):

	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	seconds = (clock.hour * 60 + clock.minute) * 60 + clock.second
	hour = clock.hour
	year = clock.year 
	month = clock.month
	day = clock.day
	if seconds % 3600 == 0: # can add error flag if it skips an hour just assume it works
		
		global prev_year
		global prev_month
		global monthly_results_dict_meter

	
		if prev_month != month:
			for index, meter in enumerate(meter_list):
				#updates the monthly_results_dict_meter and meter_results for each meter.


				bill = gridlabd.get_object("bill_" + meter["name"]) # might not have bill object
				bill_name = bill["name"]

				total_charges = to_float(gridlabd.get_value(bill_name,"total_charges"))
				total_usage = to_float(gridlabd.get_value(bill_name,"total_usage"))
				total_power = to_float(gridlabd.get_value(bill_name,"total_power"))
				logging.debug(f"total_charges = {total_charges}")
				print_a = monthly_results_dict_meter["charges"][index]
				logging.debug(f"dict = {print_a}")

				charges_current_month = total_charges - monthly_results_dict_meter["charges"][index]
				usage_current_month = total_usage - monthly_results_dict_meter["usage"][index]
				power_current_month = total_power - monthly_results_dict_meter["power"][index]
				logging.debug(f"total_charges_current month = {charges_current_month}")

				update_monthly_results_dict_meter(total_charges, total_usage,total_power,index)
				update_meter_results(charges_current_month, usage_current_month, power_current_month, index, prev_month-1)
			prev_month = month
		global prev_day
		for meter_obj in meter_list:
			meter_bill = gridlabd.get_object("bill_" + meter_obj["name"])
			update_bill_values(meter_bill, meter_obj, clock, prev_day)
		for triplex_meter_obj in triplex_meter_list:
			# updates bills of each triplex meter.
			triplex_bill = gridlabd.get_object("bill_" + triplex_meter_obj["name"])
			update_bill_values(triplex_bill,triplex_meter_obj,clock, prev_day)
			#print(str(index) +" " + str(gridlabd.get_value(triplex_bill["name"],"total_charges")) + "\n")
		prev_day = day 
	else:
		d=0
		# Add here if verbose is on print this?
		#print("Time passed was not a complete hour. Billing unchanged")

	return gridlabd.NEVER

def plot_meter_graphs(current_year_results, meter_name):
	# Outputs a pdf of 3 graphs (charges, usage, power) for a certain meter. 

	def multiple_plot(X,Y, y_label):
		fig = plt.figure()
		fig.set_size_inches(15, 8)
		plt.clf()
		ax = fig.add_axes([0,0,1,1])
		ax.bar(X,Y)
		plt.xlabel('Months')
		plt.ylabel(y_label)
		plt.title(meter_name + f" Monthly {y_label}")
		pdf.savefig(bbox_inches="tight", dpi=150)
	months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	results_charges = current_year_results[CHARGES_INDEX]
	results_usage = current_year_results[USAGE_INDEX]
	results_power = current_year_results[POWER_INDEX]
	pdf = PdfPages("results_" + str(meter_name) + ".pdf")
	multiple_plot(months, results_charges, "Charges ($)")
	multiple_plot(months, results_usage, "Usage (kWh)")
	multiple_plot(months, results_power, "Power (W)")
	pdf.close()

def plot_triplex_meter_histograms(charges_triplex_results_list, usage_triplex_results_list, peak_power_triplex_results_list):
	# Outputs histogram for distribution of all triplex meters for charges, usage, and power. 
	def multiple_plot_triplex(X, x_label):
		#figs, axs = plt.subplots(1,1, figsize=(10,7), tight_layout = True)
		fig = plt.figure()
		plt.clf()
		NBR_BINS = freedman_diaconis(X, returnas="bins")
		ax = fig.add_axes([0,0,1,1])
		for axis in [ax.xaxis, ax.yaxis]:
			axis.set_major_locator(ticker.MaxNLocator(integer=True))
		ax.hist(X, bins = NBR_BINS, edgecolor = "black")
		plt.xlabel(x_label)
		plt.ylabel('Number of triplex meters')
		plt.title("Distribution of " + x_label + " of Triplex Meters")
		pdf.savefig(bbox_inches="tight", dpi=150)
	pdf = PdfPages("triplex_results" + ".pdf")
	multiple_plot_triplex(charges_triplex_results_list, "Charges ($)")
	multiple_plot_triplex(usage_triplex_results_list, "Usage (kWh)")
	multiple_plot_triplex(peak_power_triplex_results_list, "Peak Power (W)")
	pdf.close()



def on_term(t):
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	year = clock.year 
	month = clock.month

	for index, meter in enumerate(meter_list):
		# updates each meter for the current month (when simulation ends in middle of month)
		bill = gridlabd.get_object("bill_" + meter["name"]) # might not have bill object
		bill_name = bill["name"]
		total_charges = to_float(gridlabd.get_value(bill_name,"total_charges"))
		total_usage = to_float(gridlabd.get_value(bill_name,"total_usage"))
		total_power = to_float(gridlabd.get_value(bill_name,"total_power"))

		charges_current_month = total_charges - monthly_results_dict_meter["charges"][index]
		usage_current_month = total_usage - monthly_results_dict_meter["usage"][index]
		power_current_month = total_power - monthly_results_dict_meter["power"][index]

		update_monthly_results_dict_meter(total_charges, total_usage,total_power,index)
		update_meter_results(charges_current_month, usage_current_month, power_current_month, index, month-1)



	# bill = gridlabd.get_object("bill_triplex_meter3")
	# bill_name = bill["name"]
	# triplex_meter = gridlabd.get_object("triplex_meter3")
	# meter_name = triplex_meter["name"]




	

	for index, result in enumerate(results_list_meter):
		# plot bar graph for each meter 
		plot_meter_graphs(result, meter_list[index]["name"])
	# Search for floating point 
	# total_charges = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_charges")))
	# total_usage = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_usage")))
	# billing_hrs = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"billing_hrs")))
	# total_power = re.search("\d+[\.]?[\d+]*", str(gridlabd.get_value(bill_name,"total_power")))

	# get results for all triplex meters 
	charges_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"total_charges")) for x in triplex_meter_list]

	usage_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"total_usage")) for x in triplex_meter_list]

	peak_power_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"peak_power")) for x in triplex_meter_list]

	names_triplex_meter_list = [x["name"] for x in triplex_meter_list]

	total_power_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"total_power")) for x in triplex_meter_list]

	# get resutls for all meters

	charges_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"total_charges")) for x in meter_list]

	usage_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"total_usage")) for x in meter_list]

	peak_power_meter_list = ["NaN" for x in meter_list]

	names_meter_list = [x["name"] for x in meter_list]

	total_power_meter_list = [to_float(gridlabd.get_value("bill_" + x["name"],"total_power")) for x in meter_list]



	print(charges_triplex_meter_list)

	print(usage_triplex_meter_list)

	print(peak_power_triplex_meter_list)

	print(charges_meter_list)

	print(usage_meter_list)

	print(peak_power_meter_list)

	plot_triplex_meter_histograms(charges_triplex_meter_list, usage_triplex_meter_list, peak_power_triplex_meter_list)

	# instead of getting it from the bill, sum up the values from all the meters 
	# total_charges_split = str(gridlabd.get_value(bill_name,"total_charges")).split(" ")
	# total_usage_split = str(gridlabd.get_value(bill_name,"total_usage")).split(" ")
	# billing_hrs = str(gridlabd.get_value(bill_name,"billing_hrs")) # no split because get_value does not return a unit
	# total_power_split = str(gridlabd.get_value(bill_name,"total_power")).split(" ")



	#print("Total charges:", gridlabd.get_value(bill_name,"total_charges"), "Total usage:", gridlabd.get_value(bill_name,"total_usage"), "Total hrs:", gridlabd.get_value(bill_name,"billing_hrs"), "Total power:", gridlabd.get_value(bill_name,"total_power"))
	# Removes + sign at the beginning of string
	#df = pandas.DataFrame([[total_charges_split[0][1:], total_charges_split[1]], [total_usage_split[0][1:], total_usage_split[1]], [billing_hrs[1:], "hrs"], [total_power_split[0][1:], total_power_split[1]]], ["Total Charges", "Total Usage", "Total Duration", "Total Power"],["Value", "Units"])
	charges_meter_list.extend(charges_triplex_meter_list)
	usage_meter_list.extend(usage_triplex_meter_list)
	peak_power_meter_list.extend(peak_power_triplex_meter_list)
	names_meter_list.extend(names_triplex_meter_list)
	total_power_meter_list.extend(total_power_triplex_meter_list)

	df = pandas.DataFrame({"Meter_ID": names_meter_list})
	df["Charges ($)"] = charges_meter_list
	df["Usage (kWh)"] = usage_meter_list
	df["Peak Power (W)"] = peak_power_meter_list
	df["Total Power (W)"] = total_power_meter_list
	print(df)
	df.to_csv('output.csv')






	# Add writing to own csv here?
	# Could use on exit in terminal and look at json file maybe?
	return None
