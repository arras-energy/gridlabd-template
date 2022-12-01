# convert CSV files to TEX table

import os, sys
import pandas
import re

escape_re = re.compile(r'([%$#&_])')

def escape(s):
	return escape_re.sub(r'\\\1',str(s))

for file in sys.argv[1:]:
	csv = pandas.read_csv(file).dropna(axis=0)
	align = 'c'*len(csv.columns) 
	template = escape(file.split('/')[3])
	model = escape(' '.join(file.split('/')[7:9]))
	data = escape(os.path.splitext(file.split('/')[9])[0])
	print("{{\\footnotesize")
	print(f"\\begin{{longtable}}{{|{'|'.join(align)}|}}")
	print(f"\\caption{{Validation data for {template} {model} {data}}}",'\\\\','\\hline')
	print(' & '.join(["\\textbf{"+escape(x)+"}" for x in csv.columns]), '\\\\', '\\hline','\\endhead')
	for n, row in csv.iterrows():
		print(' & '.join([escape(x) for x in row]), '\\\\', '\\hline')
	print("\\end{longtable}")
	print('}}')