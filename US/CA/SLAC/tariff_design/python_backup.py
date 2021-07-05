import csv
import pandas


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
    import os
    global data_list
    i=0

    # import in tariff data from API
    if not os.path.exists('usurdb.csv'):
        import shutil
        import requests
        url = "https://openei.org/apps/USURDB/download/usurdb.csv.gz"
        filename = url.split("/")[-1]
        fgzip = gzip.open(filename,'rb')
        with gzip.open(filename, 'r') as f_in, open('usurdb.csv', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    pandas.set_option("max_rows",None)
    pandas.set_option("max_columns",None)
    data = pandas.read_csv("usurdb.csv",low_memory=False)


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
    gridlabd.setvalue(meter["measured_real_energy_delta"],"measured_real_energy_delta", str(3600))
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

    # Need to add daily calculation and use if exist to account for NAN?
  if gridlabd.get_value(tariff_name, string+'_tier0') not None and daily_usage <= to_float(gridlabd.get_value(tariff_name, string+'_tier0')):
            rate0 = to_float(get_value(tariff_name, string+'_rate0'))
            charges = energy_hr * rate0
        elif gridlabd.get_value(tariff_name, string+'_tier0') is None:
            rate0 = to_float(get_value(tariff_name, string+'_rate0'))
            charges = energy_hr * rate0
        elif gridlabd.get_value(tariff_name, string+'_tier1') not None and daily_usage <= to_float(gridlabd.get_value(tariff_name, string+'_tier1')):
            rate0 = to_float(gridlabd.get_value(tariff_name,string+'_rate0'))
            rate1 = to_float(gridlabd.get_value(tariff_name,string+'_rate1'))
            tier0 = (daily_usage - to_float(gridlabd.get_value(tariff_name, string+'_tier0')))
            tier1 = energy_hr-tier0
            charges =  tier0 * rate0 + tier1 * rate1
        elif gridlabd.get_value(tariff_name, string+'_tier1') is None:

        elif gridlabd.get_value(tariff_name, string+'tier2') not None and daily_usage <= to_float(get_value(tariff_name, string+'_tier2')):
            rate1 = to_float(gridlabd.get_value(tariff_name,string+'rate1'))
            rate2 = to_float(gridlabd.get_value(tariff_name,string+'rate2'))
            tier1 = (daily_usage - to_float(gridlabd.get_value(tariff_name, string+'tier1')))
            tier2 = energy_hr-tier1
            charges =  tier1 * rate1 + tier2 * rate2
        elif gridlabd.get_value(tariff_name, string+'_tier3') not None and daily_usage <= to_float(get_value(tariff_name, string+'_tier3')) >:
            rate2 = to_float(gridlabd.get_value(tariff_name,string+'rate2'))
            rate3 = to_float(gridlabd.get_value(tariff_name,string+'rate3'))
            tier2 = (daily_usage - to_float(gridlabd.get_value(tariff_name, string+'tier2')))
            tier3 = energy_hr-tier0
            charges =  tier2 * rate2 + tier3 * rate3
        elif gridlabd.get_value(tariff_name, string+'tier3') not None daily_usage > to_float(gridlabd.get_value(tariff_name, string+'_tier3')):
            rate4 = to_float(gridlabd.get_value(tariff_name, string+'rate4'))
            charges = energy_hr * rate4
        else:
            print("ERROR: No charge calculated")

    else:
        print("Time passed was not a complete hour. Billing unchanged")
    
    return 

    # Work on monthly bill implementation
    total_bill = charge + monthly_mincharge + monthly_fixedchargefirstmeter

    gridlabd.set_value(bill_name,"energy_charges", str(charge))
    gridlabd.set_value(bill_name,"total_bill", str(total_bill))


    return 



'''
def get_data(**kwargs):

    # read in data from user csv
    # hard coded for now
    utility_name = "Pacific Gas & Electric Co"       #kwargs['utility']
    sector_type = "Residential"      #kwargs['sector']
    tariff_name = "E-TOU Option A - Residential Time of Use Service Baseline Region Z" #kwargs['name']

    # query OpenEl database
    # change this to work with API not csv?
    
    pandas.set_option("max_rows",None)
    pandas.set_option("max_columns",None)
    data = pandas.read_csv("../../../../../usurdb.csv",low_memory=False)

    utility = data[data.utility==utility_name]
    utility_active = utility[utility["enddate"].isna()]
    tariff = {}
    for sector in pandas.unique(utility_active['sector']):
        tariff[sector] = utility_active[utility_active['sector']==sector].dropna(how='all',axis=1)

    tariff_data = tariff[sector_type].query('name==@tariff_name').transpose()

    # read rates -- improve this efficieny
    # 1. Expand to all periods
    # Check if values are NaN before separating?

    period_0_rates = tariff_data.loc[['energyratestructure/period0/tier0rate',
                            'energyratestructure/period0/tier1rate',
                            'energyratestructure/period0/tier2rate',
                            'energyratestructure/period0/tier3rate',
                            'energyratestructure/period0/tier4rate']]
    period_1_rates = tariff_data.loc[['energyratestructure/period1/tier0rate',
                            'energyratestructure/period1/tier1rate',
                            'energyratestructure/period1/tier2rate',
                            'energyratestructure/period1/tier3rate',
                            'energyratestructure/period1/tier4rate']]
    period_2_rates = tariff_data.loc[['energyratestructure/period0/tier0rate',
                                'energyratestructure/period2/tier1rate',
                                'energyratestructure/period2/tier2rate',
                                'energyratestructure/period2/tier3rate',
                                'energyratestructure/period2/tier4rate']]
    period_3_rates = tariff_data.loc[['energyratestructure/period3/tier0rate',
                                'energyratestructure/period3/tier1rate',
                                'energyratestructure/period3/tier2rate',
                                'energyratestructure/period3/tier3rate',
                                'energyratestructure/period3/tier4rate']]
    period_0_rates_ls = period_0_rates.squeeze().dropna().tolist()
    period_1_rates_ls = period_1_rates.squeeze().dropna().tolist()
    period_2_rates_ls = period_2_rates.squeeze().dropna().tolist()
    period_3_rates_ls = period_3_rates.squeeze().dropna().tolist()
    
    
    schedule = tariff_data.loc[]
    schedule_dict = {'0L':period_0_rates_ls, '1L':period_1_rates_ls, '2L':period_2_rates_ls,
                 '3L':period_3_rates_ls}
    
    # inputting data into gridlabd
    # edit this to reflect tiers
    
    gridlabd.set_value(tariff_name, "period_0_rates", period_0_rates)
    
    
    print(schedule_dict)

    return schedule_dict
'''
        


