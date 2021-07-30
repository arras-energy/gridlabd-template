import pandas as pd 
import string
import math
import re


excel = 'Pole_Output_Sample.xls'

# Round to nearest hundreth decimal place if value has more decimal places than that. 
decimal_rounding = 2 

# Read all the sheets in the .xls file 
df = pd.read_excel(excel, sheet_name=None)  


# The first row of each xls file is the header so we convert it to header.  
for key in df: 
	new_header = df[key].iloc[0] 
	df[key] = df[key][1:]
	df[key].columns = new_header 



# First do operations on the sheet 'Design - Pole.'
df_current_sheet = df['Design - Pole'] 
# Drop unneeded columns 
df_current_sheet.drop(['Owner', 'Foundation', 'Ground Water Level',], 
					  axis=1, 
					  inplace=True)

def parse_angle(cell_string, current_column, current_row):
	"""Parse a string to get a string with angle in a unit that is supported by Gridlabd

	Additional acceptable units can be added to angle_units. Invalid inputs raise a ValueError. 

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
	value = re.search("\d+[\.]?[\d+]*", cell_string)
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	output_unit = ""
	for unit in angle_units.keys():
		if unit in cell_string:
			output_unit = angle_units[unit]
			break
	if output_unit == "": 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')
	elif value == None: 
		raise ValueError(f'Please specify valid value for {cell_string} in column: {current_column}, row {current_row}.')
	else:
		return value.group() + " " + output_unit
	

def parse_length(cell_string, current_column, current_row):
	"""Parse a string to get a string with length in a unit that is supported by Gridlabd

	Additional acceptable units can be added to length_units and length_conversion with its corresponding conversion value to degrees. 
	Supports multiple units in one string. Invalid inputs raise a ValueError. 

    Keyword arguments:
    cell_string -- the string to be parsed (presumably from a cell)
    current_column -- the column of the cell it is parsing. For more descriptive ValueErrors
    current_row -- the row of the cell it is parsing. For more descriptive ValueErrors
    """
	INCH_TO_FEET = 0.0833
	UNIT_TO_UNIT = 1.0 
	YARD_TO_FEET = 3.0
	MILE_TO_FT = 5280.0 
	FEET_TO_INCH = 12.0
	YARD_TO_INCH = 36.0
	MILE_TO_INCH = 6360.0
	MILE_TO_YARD = 1760.0
	# Handle values and units in different orders.
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
    # Map to a dictionary of conversion rates of different units to the key of length_conversions.
	length_conversions = {	
	"ft" : {"in" : INCH_TO_FEET, "ft" :  UNIT_TO_UNIT, "yd" : YARD_TO_FEET, "mile" : MILE_TO_FT},
    "in" : {"in" : UNIT_TO_UNIT,"ft": FEET_TO_INCH,  "yd": YARD_TO_INCH, "mile" : MILE_TO_INCH},
    "yd" : {"in": 1/YARD_TO_INCH, "ft": 1/YARD_TO_FEET, "yd": UNIT_TO_UNIT, "mile" : MILE_TO_YARD},
    "mile" : {"in": 1/MILE_TO_INCH, "ft": 1/MILE_TO_FT, "yd": 1/MILE_TO_YARD, "mile" : UNIT_TO_UNIT}
    }
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')

	# Keeps track of the units that are in the cell. Whichever unit is listed first in length_units AND is present in the string is the unit that will be used as the output.
	cell_units = []
	
	for key in length_units.keys():
		if key in cell_string:
			cell_units.append(length_units[key]) 

	cell_numbers = re.findall('\d+[\.]?[\d+]*', cell_string)

	if len(cell_numbers) != len(cell_units):
		raise ValueError(f'Please make sure there are the same number of numbers and units for value {cell_string} in column: {current_column}, row {current_row}')

	if len(cell_units) == 0: 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')


	# Convert all the units and values in the cell to one unit and value.
	total_cell_value = 0
	for i in range(0,len(cell_numbers)):
		convert_to = length_conversions[cell_units[0]]
		total_cell_value += float(cell_numbers[i]) * convert_to[cell_units[i]]
		

	return str(round(total_cell_value,decimal_rounding)) + " " + cell_units[0]

def parse_pressure(cell_string, current_column, current_row):
	"""Parse a string to get a string with pressure in a unit that is supported by Gridlabd

	Additional acceptable units can be added to pressure_units. Invalid inputs raise a ValueError. 

    Keyword arguments:
    cell_string -- the string to be parsed (presumably from a cell)
    current_column -- the column of the cell it is parsing. For more descriptive ValueErrors
    current_row -- the row of the cell it is parsing. For more descriptive ValueErrors
    """
	pressure_units = {
	"psi" : "psi",
	"lb/in²" : "psi",
	"bar" : "bar",
	"atm" : "atm", 
	}
	value = re.search("\d+[\.]?[\d+]*", cell_string)
	if cell_string == "nan":
		raise ValueError(f'The cell column: {current_column}, row {current_row} is empty. Please enter a value.')
	output_unit = ""
	for unit in pressure_units.keys():
		if unit in cell_string:
			cell_string = cell_string.replace(unit,pressure_units[unit])
			output_unit = pressure_units[unit]
			break
	if output_unit == "": 
		raise ValueError(f'Please specify valid units for {cell_string} in column: {current_column}, row {current_row}.')
	elif value == None: 
		raise ValueError(f'Please specify valid value for {cell_string} in column: {current_column}, row {current_row}.')
	else:
		return  value.group() + " " + output_unit
	
def parse_column(df_current_sheet, current_column, parsing_function):
	"""Parse each cell in the column with a function 
	For invalid inputs, resulting cell will be "nan".
    Keyword arguments:
    current_column -- the string to be parsed (presumably from a cell)
    parsing_function -- the function to be called for each cell
    """
	for row in range(1,len(df_current_sheet[current_column])+1):
		try: 
			df_current_sheet.at[row,current_column] = parsing_function(str(df_current_sheet.at[row,current_column]),current_column,row)
		except ValueError as e: 
			df_current_sheet.at[row,current_column] = "nan"
			print(e)

def subtract_length_columns(minuend_string, subtrahend_string, minuend_column, subtrahend_column,current_row):
	"""Subtract the lengths of strings contained in two cells 

    Keyword arguments:
    minuend_string -- the string containing the minuend 
    subtrahend_string -- the string containing the subtrahend 
    minuend_column -- the name of the column containing the minuend cell. For more descriptive ValueErrors
    subtrahend_column -- the name of the column containing the subtrahend cell. For more descriptive ValueErrors
    current_row -- the row number containing the minuend cell. For more descriptive ValueErrors
    """
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
	if minuend_string == "nan":
		raise ValueError(f'The cell column: {minuend_column}, row {current_row} is empty. Please enter a value.')
	elif subtrahend_string == "nan": 
		raise ValueError(f'The cell column: {subtrahend_column}, row {current_row} is empty. Please enter a value.')
	output_unit = ""
	for unit in length_units.keys():
		if unit in minuend_string and subtrahend_string:
			output_unit = length_units[unit]
			break
	if output_unit == "": 
		raise ValueError(f'Please provide {minuend_column} and {subtrahend_column}, row {current_row} with the same units.')
	else:
		return str(round(float(re.search("^[1-9]\d*(\.\d+)?", minuend_string).group()) - float(re.search("^[1-9]\d*(\.\d+)?", subtrahend_string).group()),decimal_rounding)) + " " + output_unit


# Parse necessary columns into a format supported by Gridlabd.
parse_column(df_current_sheet, 'Lean Angle', parse_angle)
parse_column(df_current_sheet, 'Lean Direction', parse_angle)
parse_column(df_current_sheet, 'Length', parse_length)
parse_column(df_current_sheet, 'GLC', parse_length)
parse_column(df_current_sheet, 'AGL', parse_length)
parse_column(df_current_sheet, 'Effective Stress Adjustment', parse_pressure)

# Subtract agl from length to get depth. 
for row in range(1,len(df_current_sheet['AGL'])+1):
	try: 
		df_current_sheet.at[row,'AGL'] = subtract_length_columns(str(df_current_sheet.at[row,'Length']), str(df_current_sheet.at[row,'AGL']), 'Length', 'AGL', row)

	except ValueError as e: 
		df_current_sheet.at[row,'AGL'] = "nan"
		print(e) 






# Rename columns to its corresponding column name in Gridlabd.
df_current_sheet.rename(columns = {'Lean Angle': 'tilt_angle', 
	'Lean Direction': 'tilt_direction', 'Effective Stress Adjustment': 'fiber_strength', 'Length' : 'length', 'GLC' : 'ground_diameter', 'AGL' : 'depth'}, inplace=True)
# Split GPS Point into longitude and latitude 
df_current_sheet[['latitude','longitude']] = df_current_sheet['GPS Point'].str.split(' , ', expand=True)
# Remove original GPS Point column
df_current_sheet.drop(columns = {'GPS Point', 'Allowable Stress Adjustment'},axis=1,inplace=True)

#Todo 
#Handle Species column. It is a property in pole_library_config rather than pole_vulnerability_config. 

#last column called class based on what your converting. If it's pole object, powerflow.pole. If it's config, powerflow.pole_configuration. 
#don't split the csv files. Have it all in one place and differentiate it with a new column 

# Secondly, do operations on the sheet 'Design - Structure.'
df_current_sheet = df['Design - Structure'] 

parse_column(df_current_sheet, 'Height', parse_length)
parse_column(df_current_sheet, 'Offset/Lead', parse_length)
# There's a direction for the previous and next poles, but I don't see anything in pole_mount.cpp. It only has pole_spacing, 
# and it is only the mean of next and previous when xls file specifies different distances. 
# Do I handle the weight and 
parse_column(df_current_sheet, 'Direction', parse_angle)

# Comment out some columns
df_current_sheet.rename(columns = {'ID#': '//ID#', 
	'Owner': '//Owner', 'Type': '//Type', 'Related' : '//Related'}, inplace=True)




# Finally create the csv files. 

for key in df: 
	df[key].to_csv('%s.csv' %key)

print(df_current_sheet)






