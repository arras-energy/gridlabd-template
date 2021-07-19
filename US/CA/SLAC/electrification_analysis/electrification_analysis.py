import csv 
import os
import glob
from shutil import copyfile

gas_count = 0 
elec_count = 0

config_files=[]
with open('electrification_analysis_config.csv', newline='') as csvfile : 
	fr = csv.reader(csvfile, delimiter=',', quotechar='|')
	baseline_count = []
	for row in fr : 
		if 'baseline' in row[0].strip(' ').lower() : 
			baseline_count=round(total_count*float(row[1]))
		if "Total Number of Houses per Phase" in row[0] : 
			total_count = int(row[1]) #count per phase
		elif 'Start Time' in row[0] : 
			starttime=row[1]
		elif 'Stop Time' in row[0] : 
			stoptime=row[1]
		elif 'Weather File' in row[0] : 
			weather_file=row[1]
		elif 'Run Name' in row[0] or ''==row[0] : 
			continue 
		else :
			elec_count = round(total_count*float(row[1]))
			gas_count = total_count-elec_count
			config_file_name = 'elec_config_'+str(row[0]).replace(" ", "_")+'.glm'
			config_files.append(config_file_name)
			fw = open("elec_config/"+config_file_name, 'w')
			fw.write('#define HOUSESPERPHASE=' + str(total_count))
			fw.write('\n#define STARTTIME=' + starttime)
			fw.write('\n#define STOPTIME=' + stoptime)
			fw.write('\n#define GAS_COUNT=' + str(gas_count))
			fw.write('\n#define ELEC_COUNT=' + str(elec_count))
			fw.write('\n#define WEATHER=' + weather_file)
			if baseline_count : 
				fw.write('\n#define BASELINE_COUNT=' + str(baseline_count))
			else : 
				baseline_count=round(total_count*0.50)
				fw.write('\n#print Electrification Baseline is not provided, assuming 50% electric')
			upgrade_count=elec_count-baseline_count
			fw.write('\n#define UPGRADE_COUNT=' + str(upgrade_count))