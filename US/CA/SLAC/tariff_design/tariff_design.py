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
# Pivots in pandas. Have meter output.csv separated by month. 
# ICA (Hosting capacity)- Solar - Nodes -> thermal MW, voltage, control, current. Add solar to each until one breaks.
# Same for baterry and ev charger 

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


def update_bill_values(bill, meter_name, clock, prev_day): 
	""" 
	Updates the bill values of the specific meter_name. Uses clock and previous day to reset usage in the bill. 
	This function is called every hour for each meter and triplex meter. 
	"""
	hour = clock.hour
	tariff = gridlabd.get_object("tariff")
	tariff_name = tariff["name"]
	bill_name = bill["name"]
	meter = gridlabd.get_object(meter_name)

	billing_hrs = to_float(gridlabd.get_value(bill_name, "billing_hrs"))

	# energy usage over the hour
	energy_hr =(to_float(gridlabd.get_value(meter_name, 'measured_real_energy_delta')))/1000 #kWh

	# check if in same day/ if timing needs to be updated
	day = clock.day

	# TODO: refactor to not rely on globals. Currently does not affect functionality. 
	global rates
	global schedule
	
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
		gridlabd.set_value(bill_name,"billing_hrs",str(billing_hrs + 1))
		gridlabd.set_value(bill_name, "usage", str(daily_usage))
		gridlabd.set_value(bill_name, "total_usage", str(energy_hr + to_float(gridlabd.get_value(bill_name, "total_usage"))))
		gridlabd.set_value(bill_name, "total_power", str(to_float(gridlabd.get_value(meter_name, "measured_real_power")) + to_float(gridlabd.get_value(bill_name, "total_power"))))
		gridlabd.set_value(bill_name, "peak_power", str(max(to_float(gridlabd.get_value(meter_name, "measured_real_power")), to_float(gridlabd.get_value(bill_name, "peak_power")))))
def update_monthly_cumulative_meter_results(total_charges, total_usage, total_power, meter_name):
	# updates monthly updated results of meter
	gridlabd.set_value(meter_name, "monthly_updated_charges", str(total_charges))
	gridlabd.set_value(meter_name, "monthly_updated_usage", str(total_usage)) 
	gridlabd.set_value(meter_name, "monthly_updated_power", str(total_power)) 


def update_meter_results(charges_current_month,usage_current_month,power_current_month, meter_name, month):
	# update string representation of list with each index representing a month and each element representing the results (charges, usage, power) for that month. 

	monthly_charges_list = gridlabd.get_value(meter_name, "monthly_charges").split(",")
	monthly_charges_list[month] = charges_current_month + float(monthly_charges_list[month])
	gridlabd.set_value(meter_name, "monthly_charges", ",".join([str(element) for element in monthly_charges_list]))

	monthly_usage_list = gridlabd.get_value(meter_name, "monthly_usage").split(",")
	monthly_usage_list[month] = usage_current_month + float(monthly_usage_list[month])
	gridlabd.set_value(meter_name, "monthly_usage", ",".join([str(element) for element in monthly_usage_list]))

	monthly_power_list = gridlabd.get_value(meter_name, "monthly_power").split(",")
	monthly_power_list[month] = power_current_month + float(monthly_power_list[month])
	gridlabd.set_value(meter_name, "monthly_power", ",".join([str(element) for element in monthly_power_list]))

def update_meter_timestep(meter_name, timestep):
	# sets the time step of meter to timestep 
	delta = to_float(gridlabd.get_value(meter_name,"measured_energy_delta_timestep"))
	if delta != timestep:
		print("Measured real energy delta was not set to 1 hr. Setting delta to 1 hr")
		gridlabd.set_value(meter_name,"measured_energy_delta_timestep", str(timestep))

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



	t_counter = int(gridlabd.get_global("tariff_index"))

	logging.basicConfig(level=logging.DEBUG)
	logger = logging.getLogger()
	#logger.disabled = True

	global tariff_df # reads tariff on init 
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')


	# globals to keep track of previous timeframes and the list of triplex meter names and meter names 
	global prev_year
	global prev_month
	global prev_day
	global triplex_name_list
	global meter_name_list
	
	prev_day = clock.day
	obj_list = gridlabd.get("objects")
	triplex_name_list = [] # list of triplex meter objects
	meter_name_list = [] # list of meter objects
	for obj in obj_list:
		data = gridlabd.get_object(obj)
		if data["class"] == "triplex_meter":
			triplex_name_list.append(obj) # appends the name of the triplex meter rather than the actual object 
			update_meter_timestep(obj, 3600) # meter time step to be an hour 
		if data["class"] == "meter":
			meter_name_list.append(obj)
			update_meter_timestep(obj, 3600)


	monthly_initial_list = "0,0,0,0,0,0,0,0,0,0,0,0" # a string representation of list. Each index represents a month. Each value represents result of that month. 
	for meter_name in meter_name_list:
		# initialize values for each meter 
		gridlabd.set_value(meter_name, "monthly_charges", monthly_initial_list)
		gridlabd.set_value(meter_name, "monthly_usage", monthly_initial_list)
		gridlabd.set_value(meter_name, "monthly_power", monthly_initial_list)

		gridlabd.set_value(meter_name, "monthly_updated_charges", "0.0")
		gridlabd.set_value(meter_name, "monthly_updated_usage", "0.0")
		gridlabd.set_value(meter_name, "monthly_updated_power", "0.0")


	prev_year = clock.year # initialize to start of clock 
	prev_month = clock.month
	
	try:
		tariff_df = read_tariff("tariff_library_config.csv", t_counter) # Could edit to allow user to input csv path?
	except ValueError as e:
		gridlabd.error(str(e))
		sys.exit(1) 

	return True



def on_commit(t):
	# Update all meters and triplex meters each hour. Also updates monthly values for meters every new month. 
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	seconds = (clock.hour * 60 + clock.minute) * 60 + clock.second
	hour = clock.hour
	year = clock.year 
	month = clock.month
	day = clock.day
	if seconds % 3600 == 0: 
		
		global prev_year
		global prev_month

	
		if prev_month != month:
			for index, meter_name in enumerate(meter_name_list):
				# update meter and meter bill values 
			
				bill = gridlabd.get_object("bill_" + meter_name) # might not have bill object
				bill_name = bill["name"]

				total_charges = to_float(gridlabd.get_value(bill_name,"total_charges"))
				total_usage = to_float(gridlabd.get_value(bill_name,"total_usage"))
				total_power = to_float(gridlabd.get_value(bill_name,"total_power"))
				logging.debug(f"total_charges = {total_charges}")

				charges_current_month = total_charges - to_float(gridlabd.get_value(meter_name, "monthly_updated_charges"))
				usage_current_month = total_usage - to_float(gridlabd.get_value(meter_name, "monthly_updated_usage"))
				power_current_month = total_power - to_float(gridlabd.get_value(meter_name, "monthly_updated_power"))
				logging.debug(f"total_charges_current month = {charges_current_month}")

				update_monthly_cumulative_meter_results(total_charges, total_usage,total_power,meter_name)
				update_meter_results(charges_current_month, usage_current_month, power_current_month, meter_name, prev_month-1)
			prev_month = month
		global prev_day
		for meter_name in meter_name_list:
			# update bill values for each meter
			meter_bill = gridlabd.get_object("bill_" + meter_name)
			update_bill_values(meter_bill, meter_name, clock, prev_day)
		for triplex_meter_name in triplex_name_list:
			# updates bill values of each triplex meter.
			triplex_bill = gridlabd.get_object("bill_" + triplex_meter_name)
			update_bill_values(triplex_bill,triplex_meter_name,clock, prev_day)
		prev_day = day 
	else:
		d=0
		# Add here if verbose is on print this?
		#print("Time passed was not a complete hour. Billing unchanged")

	return gridlabd.NEVER

def plot_meter_graphs(meter_name):
	# Outputs a pdf of 3 graphs (charges, usage, power) for a certain meter. Uses the properties monthly_charges, monthly_usage, monthly_power 

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
	results_charges = [float(month_value) for month_value in gridlabd.get_value(meter_name, "monthly_charges").split(",")]
	results_usage = [float(month_value) for month_value in gridlabd.get_value(meter_name, "monthly_usage").split(",")]
	results_power = [float(month_value) for month_value in gridlabd.get_value(meter_name, "monthly_power").split(",")]
	logging.debug(results_charges)
	pdf = PdfPages("results_" + str(meter_name) + ".pdf")
	multiple_plot(months, results_charges, "Charges ($)")
	multiple_plot(months, results_usage, "Usage (kWh)")
	multiple_plot(months, results_power, "Power (W)")
	pdf.close()

def plot_triplex_meter_histograms(charges_triplex_results_list, usage_triplex_results_list, peak_power_triplex_results_list):
	# Outputs histogram for distribution of all triplex meters for charges, usage, and power. 
	def multiple_plot_triplex(X, x_label):
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

	for index, meter_name in enumerate(meter_name_list):
		# updates each meter for the current month (when simulation ends in middle of month)
		bill = gridlabd.get_object("bill_" + meter_name)
		bill_name = bill["name"]
		total_charges = to_float(gridlabd.get_value(bill_name,"total_charges"))
		total_usage = to_float(gridlabd.get_value(bill_name,"total_usage"))
		total_power = to_float(gridlabd.get_value(bill_name,"total_power"))

		charges_current_month = total_charges - to_float(gridlabd.get_value(meter_name, "monthly_updated_charges"))
		usage_current_month = total_usage - to_float(gridlabd.get_value(meter_name, "monthly_updated_usage"))
		power_current_month = total_power - to_float(gridlabd.get_value(meter_name, "monthly_updated_power"))

		update_monthly_cumulative_meter_results(total_charges, total_usage,total_power, meter_name)
		update_meter_results(charges_current_month, usage_current_month, power_current_month, meter_name, month-1)






	

	for meter_name in meter_name_list:
		# plot bar graph for each meter 
		plot_meter_graphs(meter_name)

	# get results for all triplex meters 
	charges_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + triplex_name,"total_charges")) for triplex_name in triplex_name_list]
	usage_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + triplex_name,"total_usage")) for triplex_name in triplex_name_list]
	peak_power_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + triplex_name,"peak_power")) for triplex_name in triplex_name_list]
	total_power_triplex_meter_list = [to_float(gridlabd.get_value("bill_" + triplex_name,"total_power")) for triplex_name in triplex_name_list]

	# get resutls for all meters
	charges_meter_list = [to_float(gridlabd.get_value("bill_" + meter_name,"total_charges")) for meter_name in meter_name_list]
	usage_meter_list = [to_float(gridlabd.get_value("bill_" + meter_name,"total_usage")) for meter_name in meter_name_list]
	peak_power_meter_list = ["NaN" for x in meter_name_list]
	total_power_meter_list = [to_float(gridlabd.get_value("bill_" + meter_name,"total_power")) for meter_name in meter_name_list]



	plot_triplex_meter_histograms(charges_triplex_meter_list, usage_triplex_meter_list, peak_power_triplex_meter_list)

	# appends meter list and its results to triplex meter list and its results
	charges_meter_list.extend(charges_triplex_meter_list)
	usage_meter_list.extend(usage_triplex_meter_list)
	peak_power_meter_list.extend(peak_power_triplex_meter_list)
	meter_name_list.extend(triplex_name_list)
	total_power_meter_list.extend(total_power_triplex_meter_list)

	# add to dataframe by column 
	df = pandas.DataFrame({"Meter_ID": meter_name_list})
	df["Charges ($)"] = charges_meter_list
	df["Usage (kWh)"] = usage_meter_list
	df["Peak Power (W)"] = peak_power_meter_list
	df["Total Power (W)"] = total_power_meter_list
	print(df)
	df.to_csv('output.csv')

	return None
