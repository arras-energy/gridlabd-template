import pandas as pd 

#read all the sheets in the .xls file 
df = pd.read_excel('Pole_Output_Sample.xls', sheet_name=None)  

#the first row of each xls file is the header so we convert it to header.  
for key in df: 
	new_header = df[key].iloc[0] #grab the first row for the header
	df[key] = df[key][1:] #grab  just the row after the first rows
	df[key].columns = new_header #set the header row as the df header



#extract necessary information from each sheet by deleting some of the columns 


df['Design - Pole'].drop(['Owner', 'Foundation', 'Ground Water Level', 'GPS Point'], axis=1, inplace=True)


#finally create the csv files 
for key in df: 
	df[key].to_csv('%s.csv' %key)

print(df['Design - Pole'])

