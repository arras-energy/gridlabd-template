import pandas as pd 
import csv
import numpy as np

hrs = 8760 
# def import_energy_meter () :
# 	with open("power_output/swing_power.csv", newline = '') as csvfile : 
# 		csvreader = csv.reader(csvfile)
# 		for row in csvreader : 
# 			print(', '.join(row))
# 	return yr_energy 

def import_energy_meter () :
	yr_energy = []
	with open("power_output/triplex/house_power_1.csv", newline = '') as csvfile : 
		csvreader = csv.reader(csvfile)
		for row in csvreader : 
			if "#" not in row[0] : 
				yr_energy.append(float(row[1])/1000)
	return yr_energy 

# def tou_B() :
# 	return None 

def tou_C() :
	offpeak_price_summer_tier_max = 18.6
	offpeak_price_summer_tier0 = 0.23882
	offpeak_price_summer_tier1 = 0.32068
	offpeak_price_winter_tier0 = 0.19784
	offpeak_price_winter_tier1 = 0.2797
	offpeak_price_winter_tier_max = 11.3
	peak_price_summer_tier0 = 0.30226
	peak_price_summer_tier1 = 0.38412
	peak_price_winter_tier0 = 0.21517
	peak_price_winter_tier1 = 0.29703
	delivery_price = 0.34810 
	first_day_of_summer = 152 #june 1
	last_day_of_summer = 274 #sept 30

	days = list(range(hrs))


	winter_day_prices_tier0 = [offpeak_price_winter_tier0] *16 + [peak_price_winter_tier0] *5 +  [offpeak_price_winter_tier0] *3
	summer_day_prices_tier0 = [offpeak_price_summer_tier0] *16 + [peak_price_summer_tier0] *5 +  [offpeak_price_summer_tier0] *3
	winter_day_prices_tier1 = [offpeak_price_winter_tier1] *16 + [peak_price_winter_tier1] *5 +  [offpeak_price_winter_tier1] *3
	summer_day_prices_tier1 = [offpeak_price_summer_tier1] *16 + [peak_price_summer_tier1] *5 +  [offpeak_price_summer_tier1] *3

	tier_energy = np.array(list([offpeak_price_winter_tier_max]*first_day_of_summer + [offpeak_price_summer_tier_max]*(last_day_of_summer - first_day_of_summer) + [offpeak_price_winter_tier_max] * (365-last_day_of_summer)))
	price_array_tier0 = winter_day_prices_tier0 * first_day_of_summer + summer_day_prices_tier0*(last_day_of_summer - first_day_of_summer)+  winter_day_prices_tier0 * (365-last_day_of_summer)
	price_array_tier1 = winter_day_prices_tier1 * first_day_of_summer + summer_day_prices_tier1*(last_day_of_summer - first_day_of_summer)+  winter_day_prices_tier1 * (365-last_day_of_summer)
	# df = pd.DataFrame(price_array, columns=["prices"])
	# print( df )

	yr_energy = np.array(import_energy_meter())

	yr_energy_per_day = np.add.reduceat(yr_energy, np.arange(0, len(yr_energy), 24))
	tier1_energy = np.subtract(yr_energy_per_day,tier_energy)

	
	tier_energy[tier1_energy<0]=yr_energy_per_day[tier1_energy<0]

	tier1_energy[tier1_energy<0]=0
	annual_bill = sum([a*b for a,b in zip(tier_energy,price_array_tier0)]) + sum([a*b for a,b in zip(tier1_energy,price_array_tier1)])



	# annual_bill = sum([a*b for a,b in zip(yr_energy,price_array)])
	print(annual_bill)

	return annual_bill 

# def tou_D() :
# 	return None 

def main() : 
	annual_bill = tou_C()


if __name__ == "__main__" :
	main() 