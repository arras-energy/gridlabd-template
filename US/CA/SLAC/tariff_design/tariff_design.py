import csv
import pandas

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
    
    print(schedule_dict)

    return schedule_dict
            
get_data()
        

