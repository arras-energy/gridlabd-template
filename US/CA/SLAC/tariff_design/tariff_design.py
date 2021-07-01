import gridlabd
import csv
import pandas 
import datetime

# IMPROVE THIS TO REMOVE HARD CODING?
data_list = ['name','dgrules', 'fixedchargefirstmeter','mincharge',
 'energyratestructure/period0/tier0max',
 'energyratestructure/period0/tier0rate',
 'energyratestructure/period0/tier1max',
 'energyratestructure/period0/tier1rate',
 'energyratestructure/period0/tier2max',
 'energyratestructure/period0/tier2rate',
 'energyratestructure/period0/tier3max',
 'energyratestructure/period0/tier3rate',
 'energyratestructure/period0/tier4rate',
 'energyratestructure/period1/tier0max',
 'energyratestructure/period1/tier0rate',
 'energyratestructure/period1/tier1max',
 'energyratestructure/period1/tier1rate',
 'energyratestructure/period1/tier2max',
 'energyratestructure/period1/tier2rate',
 'energyratestructure/period1/tier3max',
 'energyratestructure/period1/tier3rate',
 'energyratestructure/period1/tier4rate',
 'energyratestructure/period2/tier0max',
 'energyratestructure/period2/tier0rate',
 'energyratestructure/period2/tier1max',
 'energyratestructure/period2/tier1rate',
 'energyratestructure/period2/tier2max',
 'energyratestructure/period2/tier2rate',
 'energyratestructure/period2/tier3max',
 'energyratestructure/period2/tier3rate',
 'energyratestructure/period2/tier4rate',
 'energyratestructure/period3/tier0max',
 'energyratestructure/period3/tier0rate',
 'energyratestructure/period3/tier1max',
 'energyratestructure/period3/tier1rate',
 'energyratestructure/period3/tier2max',
 'energyratestructure/period3/tier2rate',
 'energyratestructure/period3/tier3max',
 'energyratestructure/period3/tier3rate',
 'energyratestructure/period3/tier4rate',
 'energyratestructure/period4/tier0max',
 'energyratestructure/period4/tier0rate',
 'energyratestructure/period4/tier1rate',
 'energyratestructure/period5/tier0rate',
 'energyratestructure/period6/tier0rate',
 'energyratestructure/period7/tier0rate']

def to_float(x):
	return float(x.split(' ')[0])

def to_datetime(x,format):
	return parser.parse(x)

def on_init(t):
	i=0
	global data_list

	# CHANGE TO USE REQUEST & ZIPFILE PY LIBRARY
	# import in tariff data from API
	'''
	import os
	if not os.path.exists('usurdb.csv'):
    	import os
    	os.system('curl https://openei.org/apps/USURDB/download/usurdb.csv.gz | gunzip > usurdb.csv')
	'''	
	pandas.set_option("max_rows",None)
	pandas.set_option("max_columns",None)
	data = pandas.read_csv("../../../../../usurdb.csv",low_memory=False)


	# read in csv file
	with open("tariff_library_config.csv") as fp:
		reader = csv.reader(fp, skipinitialspace=True, delimiter=",")
		next(reader)
		tariff_input = [row for row in reader]
	
	# for each tariff in csv
	for t in tariff_input:

		# get inputs from csv
		utility_name = tariff_input[i][0]
		sector_type = tariff_input[i][1]
		name = tariff_input[i][2]
		region = tariff_input[i][4]
		i = i + 1

		# parse database
		utility = data[data.utility==utility_name]
    	utility_active = utility[utility["enddate"].isna()]
   		mask = utility_active["name"].str.contains(name, regex=True, case=False) & utility_active["name"].str.contains(region, regex=True)
   		tariff_data = utility_active[mask].reset_index()

		# define gridlabd objects
		for column in data_list:
    		if tariff_data[column].isnull().values.any() == False:
       			gridlabd.setvalue(name, column, str(tariff_data.at[0,column]))
    	else:
        	continue

        # check this syntax
        energyweekdayschedule = tariff_data["energyweekdayschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True)
		gridlabd.setvalue(name, "energyweekdayschedule", str(energyweekdayschedule))
		energyweekendschedule = tariff_data["energyweekendschedule"].str.replace('[','', regex=True).str.replace(']','', regex=True)
		gridlabd.setvalue(name, "energyweekendschedule", str(energyweekendschedule))

	return True

def tariff_billing(gridlabd, **kwargs):

	# input data from fnc input and gridlab d
	# CHECK UNDERSTANDING HERE
	tariff_classname = kwargs['tariff_classname']
	tariff_name = kwargs['tariff_name']
	bill_classname = kwargs['bill_classname']
	bill_name = kwargs['bill_name']

	bill = gridlabd.get_object(bill_name)
	tariff = gridlabd.get_object(tariff_name)
	gridlabd.setvalue(tariff,bill['energy_tariff'], tariff)
	if tariff["dg_rules"] == "Net Metering":
		gridlabd.setvalue(tariff,bill['generation_tariff'],tariff)
	# else: ADD input for different generation tariff

	baseline = to_float(bill["baseline_demand"])
	meter = gridlabd.get_object(bill["meter"])

	monthly_fixedchargefirstmeter = to_float(tariff["fixedchargefirstmeter"])
	monthly_mincharge = to_float(tariff["mincharge"])

	# is this how you set the value to 1 hr?
	gridlabd.setvalue(meter["measured_real_energy_delta"],"measured_real_energy_delta", 3600)
	energy_hr = to_float(meter["measured_real_energy_delta"]/1000) #kWh

	# duration using gridlabd clock
	# need month, day, time for billing
	clock = to_datetime(gridlabd.get_global('clock'),'%Y-%m-%d %H:%M:%S %Z')
	month = clock.month
	day = clock.weekday()
	hour = clock.hour

	usage = 0.0

	# find correct rate schedule
	if (day == 5) or (day == 6):
		schedule = tariff["energyweekendschedule"]
	else:
		schedule = tariff["energyweekdayschedule"]

	idx = 24 * (month - 1) + hour
	period = schedule[idx]

	# bill calculations per hour
	if period == "1L":
		if usage < to_float(tariff["energyratestructure/period0/tier0max"]):
			usage = energy_hr + usage
			charge = energy_hr * to_float(tariff["energyratestructure/period0/tier0rate"]) + charge
		elif (usage > to_float(tariff["energyratestructure/period0/tier0max"])) and (usage < to_float(tariff["energyratestructure/period0/tier1max"])):
			usage = energy_hr + usage
			charge = energy_hr * to_float(tariff["energyratestructure/period0/tier1rate"]) + charge
		elif (usage > to_float(tariff["energyratestructure/period0/tier1max"])) and (usage < to_float(tariff["energyratestructure/period0/tier2max"])):
			usage = energy_hr + usage
			charge = energy_hr * to_float(tariff["energyratestructure/period0/tier2rate"]) + charge
		elif (usage > to_float(tariff["energyratestructure/period0/tier2max"])) and (usage < to_float(tariff["energyratestructure/period0/tier3max"])):
			usage = energy_hr + usage
			charge = energy_hr * to_float(tariff["energyratestructure/period0/tier3rate"]) + charge
		else:
			usage = energy_hr + usage
			charge = energy_hr * to_float(tariff["energyratestructure/period0/tier4rate"]) + charge
	
	
	elif period == "2L":
	elif period == "3L":
	elif period == "4L":
	elif period == "5L":
	elif period == "6L":
	elif period == "7L":
	else:

	# Work on monthly bill implementation
	total_bill = charge + monthly_mincharge + monthly_fixedchargefirstmeter

	gridlabd.set_value(bill_name,"energy_charges", str(charge))
	gridlabd.set_value(bill_name,"total_bill", str(total_bill))


	return 
