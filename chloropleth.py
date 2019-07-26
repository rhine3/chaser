import plotly
import plotly.figure_factory as ff
import pandas as pd
import os

# For county codes
state_codes = pd.read_csv('./state_codes.csv')
fips = []

# Value to color each county
values = []

# My life list
all_spp = pd.read_csv('./csvs/my_ebird_world_life_list.csv')
all_spp[['common_name', 'scientific_name']] = all_spp.Species.str.split(" - ",expand=True)
life_list = all_spp['common_name'].values 

# Desired month and frequency threshold
month = '' #'December'
percent_thresh = 0 # percentage from 0 to 1

results_folder = './county_results/'
all_csvs = [f for f in os.listdir(results_folder) if f.endswith('.csv')]

def remove_non_species(values): 
    return [spuh for spuh in values if ('.' not in spuh) and ('/' not in spuh) and ('hybrid' not in spuh) and ('Domestic' not in spuh)]

# Read each file in the obtained csvs
for csv in all_csvs:
    # Append county fip to list
    state_abbreviation = csv.split('-')[1]
    try:
        state_code = str(int(state_codes.loc[state_codes['Abbreviation'] == state_abbreviation, 'Code']))
    except:
        print(csv)
        print(state_codes.loc[state_codes['Abbreviation'] == state_abbreviation, 'Code'])
    county_code = csv.split('-')[2][0:3]
    fip = state_code + county_code
    fips.append(fip)
    
    # Get species present above a certain threshold in a certain month
    # percent_thresh = 0 and month = '' will give all data
    csv_contents = pd.read_csv(os.path.join(results_folder, csv))
    thresh_spp = csv_contents.loc[csv_contents['frequency'] > percent_thresh]
    month_spp = thresh_spp.loc[csv_contents['monthQt'].str.contains(month)]['comName'].unique()
    spp_in_county = remove_non_species(month_spp)
    
    # Makes a different map depending on what is commented out:
    
    # Append number of lifers in month in county to list
    '''lifers = set(spp_in_county) - set(life_list)
    values.append(len(lifers))'''
    
    # Append number of species in county to list
    values.append(len(spp_in_county))
    

fig = ff.create_choropleth(fips=fips, values=values)#, scope=["usa", "AK", "HI"])
fig.layout.template = None
fig.show()
