import pandas as pd 
import string
import math
import numpy as np

excel = 'Pole_Output_Sample.xls'
sheet1 = 'Design - Pole'
radians_to_degrees = 57.3

#read all the sheets in the .xls file 
df = pd.read_excel(excel, sheet_name=None)  

#the first row of each xls file is the header so we convert it to header.  
for key in df: 
	new_header = df[key].iloc[0] #grab the first row for the header
	df[key] = df[key][1:] #grab  just the row after the first rows
	df[key].columns = new_header #set the header row as the df header



#extract necessary information from each sheet 
df_current_sheet = df[sheet1] 
#droping and renaming for sheet1 
df_current_sheet.drop(['Owner', 'Foundation', 
	'Ground Water Level',], 
	axis=1, 
	inplace=True)
#renaming. Is effective stress adjustment = fiber_strength?
df_current_sheet.rename(columns = {'Lean Angle': 'tilt_angle', 
	'Lean Direction': 'tilt_direction', 'Effective Stress Adjustment': 'fiber_strength'}, inplace=True)

#filtered out any non-numbers in tilt angle and tilt direction, but in tilt_angle should be between 0 and 90 and tilt direction should be between 0 and 360 
#default unit is degrees, so stand-alone numbers will have ' deg' appended to it. If 'rad' is contained in the string, then converts the number in the string to degrees. 
#todo - handle empty cells 

current_column = 'tilt_angle'
try: 
	for i in range(1,len(df_current_sheet[current_column])+1):
		cell_value = str(df_current_sheet.at[i,current_column])
		df_current_sheet.at[i,current_column] = cell_value
		if 'rad' in cell_value:
		  df_current_sheet.at[i,current_column]= str(int(''.join(filter(str.isdigit, cell_value)))* radians_to_degrees)
		elif '°' not in cell_value and 'deg' not in cell_value: 
		  raise ValueError('Please specify units of Lean Angle to contain rad, °, or deg')
		parsed_int = int(''.join(filter(str.isdigit, cell_value)))
		if parsed_int >= 0 and parsed_int <= 90:
			df_current_sheet.at[i,current_column] = str(parsed_int) + ' deg'
		else: 
			raise ValueError('Value of Lean Angle must be between 0 and 90 degrees or 0 to 1.57 radians')
except ValueError as e: 
	print(e)


#todo - handle empty cells 
current_column = 'tilt_direction'
try: 
	for i in range(1,len(df_current_sheet[current_column])+1):
		cell_value = str(df_current_sheet.at[i,current_column])
		df_current_sheet.at[i,current_column] = cell_value
		if 'rad' in cell_value:
		  df_current_sheet.at[i,current_column]= str(int(''.join(filter(str.isdigit, cell_value)))* radians_to_degrees)
		elif '°' not in cell_value and 'deg' not in cell_value: 
		  raise ValueError('Please specify units of Lean Direction to contain rad, °, or deg')
		parsed_int = int(''.join(filter(str.isdigit, cell_value)))
		if parsed_int >= 0 and parsed_int <= 90:
			df_current_sheet.at[i,current_column] = str(parsed_int) + ' deg'
		else: 
			raise ValueError('Value of Lean Angle must be between 0 and 360 degrees or 0 to 6.28 radians')
except ValueError as e: 
	print(e)
	 




#split GPS Point into longitude and latitude 
df_current_sheet[['latitude','longitude']] = df_current_sheet['GPS Point'].str.split(',', expand=True)
#remove original GPS Point column
df_current_sheet.drop('GPS Point',axis=1,inplace=True)

#Todo 
#Handle Species column. It is a property in pole_library_config rather than pole_vulnerability_config 
#Same with Length, class, AGL, and GLC, allowable stress adjustment, and effective stress adjustment. 
#pole depth is AGL-GLC?
#Should I check for appropriate values in the cells? 
#last column called class based on what your converting. If it's pole object, powerflow.pole. If it's config, powerflow.pole_configuration. 
#don't split the csv files. Have it all in one place and differentiate it with a new column 

#finally create the csv files 

for key in df: 
	df[key].to_csv('%s.csv' %key)

print(df[sheet1])

