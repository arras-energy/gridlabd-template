import gridlabd
import csv
import pandas 

# IMPROVE THIS TO REMOVE HARD CODING?
data_list = ['dgrules', 'fixedchargefirstmeter','mincharge',
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
 'energyratestructure/period7/tier0rate',
 'energyweekdayschedule',
 'energyweekendschedule']

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
		reader = csv.reader(fp, delimiter=",")
		next(reader)
		tariff_input = [row for row in reader]
	
	for t in tariff_input:

		# get inputs from csv
		utility_name = data_read[i][0]
		sector_type = data_read[i][1]
		name = data_read[i][2]
		region = data_read[i][4]
		i = i + 1

		# parse database
		utility = data[data.utility==utility_name]
    	utility_active = utility[utility["enddate"].isna()]
   		mask = utility_active["name"].str.contains(name, regex=True, case=False) && utility_active["name"].str.contains(region, regex=False)
   		tariff_data = utility_active[mask].reset_index()

		# define gridlabd objects
		for column in data_list:
    		if tariff_data[column].isnull().values.any() == False:
       			gridlabd.setvalue(name, column, tariff_data.at[0,column])
    	else:
        	continue

	return True