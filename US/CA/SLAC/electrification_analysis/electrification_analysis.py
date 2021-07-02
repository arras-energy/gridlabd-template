import csv 
import os
import glob
from shutil import copyfile

gas_count = 0 
elec_count = 0

config_files=[]
with open('config/simulation_configuration.csv', newline='') as csvfile : 
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


for i,file_name in enumerate(config_files) : 
	if i==0 : # resetting the folder by removing all the model files 
		files = glob.glob('model_files/*')
		for f in files : 
			os.remove(f)
		del_paneldump = glob.glob('paneldump/*')
		for d in del_paneldump : 
			os.remove(d)
	copyfile('model.glm', 'model_files/model.glm')
	new_file = "model_files/model_"+file_name
	os.rename("model_files/model.glm",new_file)

	with open(new_file, 'r+') as fm:
			content = fm.read()
			fm.seek(0, 0)
			line="#include \"elec_config/" + file_name + "\"" 
			fm.write(line+"\n"+"#define RUN_NAME="+file_name[12:-4]+"\n")

del_feeder = glob.glob('output/feeder_power/*')
for f in del_feeder : 
	os.remove(f)
del_line = glob.glob('output/line_losses/*')
for f in del_line : 
	os.remove(f)
del_main = glob.glob('output/main_node_power/*')
for f in del_main : 
	os.remove(f)

