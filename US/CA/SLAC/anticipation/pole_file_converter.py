import pandas as pd 
import string
import math
import numpy as np
import re
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

def parse_angle(cell_string, current_column, current_row):
	"""Parse a string to get a string with angle in degrees

	Additional acceptable units can be added to angle_units with its corresponding conversion value to degrees. 

    Keyword arguments:
    cell_string -- the string to be parsed (presumably from a cell)
    current_column -- the column of the cell it is parsing. For more descriptive ValueErrors
    current_row -- the row of the cell it is parsing. For more descriptive ValueErrors
    """
	angle_units = {	
    "°" : "deg",
    "deg" : "deg",
    "rad" : "rad",
    "grad" : "grad",
    "quad" : "quad",
    "sr" : "sr"
	}
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	output_unit = ""
	for unit in angle_units.keys():
		if unit in cell_string:
			output_unit = angle_units[unit]
			break
	if output_unit == "": 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')
	else:
		return str(int(''.join(filter(str.isdigit, cell_string)))) + " " + output_unit
	

def parse_length(cell_string, current_column, current_row):
	INCH_TO_FEET = 0.0833
	UNIT_TO_UNIT = 1.0 
	YARD_TO_FEET = 3.0
	MILE_TO_FT = 5280.0 
	FEET_TO_INCH = 12.0
	YARD_TO_INCH = 36.0
	MILE_TO_INCH = 6360.0
	MILE_TO_YARD = 1760.0
	#handle values and units in different orders
	length_units = {	
	"'" : "ft",
    '"' : "in",
    "in" : "in",
    "inch" : "in",
    "feet" : "ft",
    "ft" : "ft",
    "foot" : "ft",
    "yd" : "yd",
    "yard" : "yd",
    "mile" : "mile",
    "mi" : "mile"
    }
    #maps to a dictionary of conversion rates of different units to the key of length_conversions
	length_conversions = {	
	"ft" : {"in" : INCH_TO_FEET, "ft" :  UNIT_TO_UNIT, "yd" : YARD_TO_FEET, "mile" : MILE_TO_FT},
    "in" : {"in" : UNIT_TO_UNIT,"ft": FEET_TO_INCH,  "yd": YARD_TO_INCH, "mile" : MILE_TO_INCH},
    "yd" : {"in": 1/YARD_TO_INCH, "ft": 1/YARD_TO_FEET, "yd": UNIT_TO_UNIT, "mile" : MILE_TO_YARD},
    "mile" : {"in": 1/MILE_TO_INCH, "ft": 1/MILE_TO_FT, "yd": 1/MILE_TO_YARD, "mile" : UNIT_TO_UNIT}
    }
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	#tries to identify the units out of all the non-numbers in the string. Very lenient. 


	cell_units = re.findall('\D+', cell_string) 
	for counter, cell_unit in enumerate(cell_units):
		for key in length_units.keys():
			if key in cell_unit:
				cell_units[counter] = length_units[key]

	cell_numbers = re.findall('\d+', cell_string)

	if len(cell_numbers) != len(cell_units):
		raise ValueError(f'Please make sure there are the same number of numbers and units for value {cell_string} in column: {current_column}, row {current_row}')

	if len(cell_units) == 0: 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')


	#converts all the units and values in the cell to one unit and value 
	total_cell_value = 0
	for i in range(0,len(cell_numbers)):
		convert_to = length_conversions[cell_units[0]]
		total_cell_value += int(cell_numbers[i]) * convert_to[cell_units[i]]
		print(convert_to[cell_units[i]])

	return str(total_cell_value) + " " + cell_units[0]

def parse_pressure(cell_string, current_column, current_row):
	pressure_units = {
	"psi" : "psi",
	"lb/in²" : "psi",
	"bar" : "bar",
	"atm" : "atm", 
	}
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	output_unit = ""
	for unit in pressure_units.keys():
		if unit in cell_string:
			cell_string = cell_string.replace(unit,pressure_units[unit])
			print(cell_string)
			output_unit = pressure_units[unit]
			break
	if output_unit == "": 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')
	else:
		return str(int(''.join(filter(str.isdigit, cell_string)))) + " " + output_unit
	
def parse_column(current_column, parsing_function):
	for row in range(1,len(df_current_sheet[current_column])+1):
		try: 
			df_current_sheet.at[row,current_column] = parsing_function(str(df_current_sheet.at[row,current_column]),current_column,row)
		except ValueError as e: 
			df_current_sheet.at[row,current_column] = "NaN"
			print(e)

#	handles row values for tilt_angle and tilt_direction including if its empty, if units are not specified, and if the value is out of bounds.
#	All values are converted to deg. 


parse_column('Lean Angle', parse_angle)
parse_column('Lean Direction', parse_angle)
parse_column('Length', parse_length)
parse_column('GLC', parse_length)
parse_column('AGL', parse_length)
parse_column('Effective Stress Adjustment', parse_pressure)




#handles row values for length including if its empty, if units are not specified, and if the value is out of bounds. 
#All values are converted to in. 

#renaming. Is effective stress adjustment = fiber_strength?
df_current_sheet.rename(columns = {'Lean Angle': 'tilt_angle', 
	'Lean Direction': 'tilt_direction', 'Effective Stress Adjustment': 'fiber_strength', 'Length' : 'length', 'GLC' : 'ground_diameter'}, inplace=True)
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




