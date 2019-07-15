import csv
import pandas as pd
import numpy as np
from geopy.distance import vincenty
import datetime
import collections
import math

def show_unique(series):
    '''
    Return a list of the unique elements in a pandas series
    '''
    
    all_elements = list(series)
    seen = set()
    seen_add = seen.add
    unique_elements = [x for x in all_elements if not (x in seen or seen_add(x))]

    return unique_elements

def identify_centers(df, radius_miles = 5):
    '''
    Create a dictionary where the
        keys = centers,
        values = list of points within the desired radius
    '''
    
    # Create a list of all unique points to use for our centers
    all_points = show_unique(df['LOCATION'])
    centers = all_points #TODO: create a more efficient center-finding algo

    my_dict = {}
    centers = all_points
    for center in centers:
        close_points = []
        for point in all_points:
            try:
                distance = vincenty(center, point, miles=True)
            except ValueError: #ValueError: Vincenty formula failed to converge!
                distance = np.NaN
            if distance < radius_miles:
                close_points.append(point)

        my_dict[center] = close_points
        
    return my_dict

def select_loc_df(df, my_dict, center): 
    '''
    Select relevant sightings by location
    
    For a single center (key), return a DF with only:
    - sightings from locations in the desired radius (value) 
    - sightings from a desired date range
    
    Inputs:
        df: the full dataframe to select sightings from
        my_dict: the dictionary associating centers with lists
            of points within the radius
        center: the specific dictionary key to use
    
    '''

    # Select only locations corresponding to radius around the center
    return df[df['LOCATION'].isin(my_dict[center])]

def select_date_df(df, month, day, interval=4): 
    '''
    Select relevant sightings by date
    
    For a single center (key), return a DF with only sightings from a desired date range
    
    Inputs:
        df: the full dataframe to select sightings from
        month, day: the date to center a date range around
        interval: the number of days before & after the specified
            date to include sightings from
    
    '''
    
    # Select only locations within date range
    desired_date=datetime.date(2019, month, day) #2019 is a placeholder year

    df['INTERVAL'] = df['OBSERVATION DATE'].apply(interval_without_year, date2=desired_date)
    selected_sightings = df.loc[df['INTERVAL'] <= interval]
    
     
    return selected_sightings


def calculate_score_total_spp(df):
    '''
    Calculate score of DF based on # species
    
    Calculate score of a DF solely by how many
    unique species are in the 'COMMON NAME' column.
    
    Inputs:
        df: a dataframe with a column 'COMMON NAME'. This df should
        contain one column for each individual observation of a species.
        
    Returns: 
    '''
    
    # Create DF associating common name with count of lists
    #(to maintain compliance with other scoring functions)
    collapsed_df = df['COMMON NAME'].value_counts()
    
    # Calculate true score
    score = len(show_unique(df['COMMON NAME']))
    
    return score, collapsed_df

def calculate_score_num_lists(df):

    '''
    Calculate score of DF based on # lists
    
    Calculate the score of a DF by finding
    the number of checklists on which a species was reported.
    This could be modified to be more sophisticated in the future.
    
    Inputs:
        df: a dataframe with a column 'COMMON NAME'. This df should
            contain one column for each individual observation of a species.
    
    Outputs:
        the sum of the number of checklists each species
        appeared on--which is identical to df.shape[0]
    '''
    
    # Create DF associating common name with count of lists
    collapsed_df = df['COMMON NAME'].value_counts()
    
    # Calculate true score
    score = sum(collapsed_df)
    
    return score, collapsed_df

def interval_without_year(date1, date2):
    '''
    Return number of days between two dates
    
    Returns interval of days between two dates regardless of year. 
    For instance, January 1, 2019 and January 4, 1999 are considered 
    3 days apart with this method, no matter which one is provided
    as day1 or day2.
    
    This function may be imperfect WRT leap years.
    
    Inputs:
        date1, date2: datetime.date objects
        
    Returns:
        number of days between them on calendar (regardless of year)
    
    '''
    date1 = date1.date()
    delta = date1-date2
    way1 = delta.days % 365
    way2 = 365-way1
    
    if way1 < way2: return way1
    else: return way2
    
    def analyze_data(
    df,
    lifelist_path,
    month,
    day,
    padding,
    radius_miles,
    scoring_method = 'total' #or 'lists'
):
    '''
    Find best area for a given month, day, and radius
    
    Inputs
        df: dataframe of eBird observations generated by import_data
        lifelist_path: path to .csv of life list file. Species should be in format:
            'Black-bellied Whistling-Duck - Dendrocygna autumnalis' (without quotes)
        month: numerical month of 'center date' around which to search for hotspots
        day: numerical day of 'center date' around which to search for hotspots
        padding: how many days before and after the 'center date' the observations should include
        radius_miles: how large of a radius do you want to search within
        scoring_method: how to score hotspots
            total: just based on the total number of species
            lists: based on how many lists each lifer appeared
        
    Returns (all_dfs, all_scores)
        all_dfs: a dataframe for every center
        all_scores: a score for every center
    '''
    
    # Generate list of lifers from .csv file
    life_list = []
    with open(lifelist_path) as f:
        reader = csv.reader(f)
        
        # Handle different eBird life list formats
        next(reader) # Skip line 0, the header
        test_bird = next(reader)[1]
        f.seek(1) # Go back to line 1, the first data row
        # For scientific names
        if ' - ' in test_bird:
            for line in reader:
                bird = ' '.join(line[1].split()[:-3])
                life_list.append(str(bird).lower()) 
                
        # For no scientific names:
        else:
            for line in reader:
                bird = line[1]
                life_list.append(str(bird).lower()) 
        
        

    # Remove species that are already on one's life list
    df = df[~df['COMMON NAME'].str.lower().isin(life_list)]
    
    
    # Remove checklists from outside of this date range
    df = select_date_df(df, month, day, interval=4)
    
    
    # Identify a dict of centers
    my_dict = identify_centers(df, radius_miles)
    
    
    # For each center, generate a relevant DF and calculate its score
    all_dfs = {}
    all_scores = {}
    for center in my_dict.keys():
        
        # Select only locations within radius
        selected_df = select_loc_df(df, my_dict, center)
        
        # Calculate score and 'collapsed DF', which is a dataframe
        # associating each species with the number of checklists it appeared on
        if scoring_method == 'lists':
            score, collapsed_df = calculate_score_num_lists(selected_df)
        else:
            score, collapsed_df = calculate_score_total_spp(selected_df)
        
        # Create dictionaries associating centers with their scores & collapsed dfs
        all_scores[center] = score
        all_dfs[center] = collapsed_df
        
    
    return (all_dfs, all_scores)

def import_data(
    engine_path,
    table_name,
):
    '''
    Import and clean dataset from database.
    
    Import a dataset from a database. Add a location column and remove
    extraneous records (spuhs, slashes, hybrids, domestics) from dataset.
    
    Inputs
        engine_path: path to db location, e.g. '/Volumes/storage/data.db'
        table_name: the name of the table in this database, e.g. 'usa_only'
        
    Returns
        a rough database
    '''
    
    # Import data
    engine = create_engine('sqlite:///' + engine_path)
    rough_df = pd.read_sql(table_name, con = engine)
    
    # Add location column
    rough_df['LOCATION'] = rough_df.apply(lambda row: (row['LATITUDE'], row['LONGITUDE']), axis=1)
    
    # Remove spuhs, slashes, domestics, and hybrids to leave only species, issf, and form
    return rough_df[~rough_df['CATEGORY'].isin(['spuh', 'domestic', 'slash', 'hybrid'])]

def chaser(
    engine_path,
    table_name,
    lifelist_filename,
    month,
    day,
    padding,
    num_spots,
    radius_miles,
    scoring_method = 'total' #or 'lists'
):
    
    '''
    Find the best places to go for your life list
    
    Inputs
        engine_path: path to database of all observations, e.g. '/Volumes/storage/all_data.db'
        table_name: name of relevant table within database, e.g. 'usa_only_table'
        lifelist_filename: path to .csv file containing a single column
            All species must be in format: 'Black-bellied Whistling-Duck - Dendrocygna autumnalis'
            To create a file like this, download your life list, then copy and paste the 'Species'
            column into a new .csv. Do not include the 'species' header (though it won't make a difference).
            Life list can be downloaded at https://ebird.org/MyEBird?cmd=lifeList&listType=world&listCategory=default&time=life
        month: numerical month in which to search for lifer spots
        day: numerical day around which to search for lifer spots
        padding: number of days before and after month/day to search for lifer spots
        num_spots: number of top spots to show
        radius_miles: miles within which you are willing to bird
    '''
    
    
    # Get DF of data
    my_df = import_data(engine_path, table_name)
    
    # Only look for places in the USA (#ABAcentrism)
    my_df = my_df[(my_df['STATE CODE'].str.contains('US-')) | (my_df['STATE CODE'].str.contains('CA-'))]

    # Get dict of dfs of highest-scoring spots
    dfs, scores = analyze_data(
        df = my_df,
        lifelist_path = lifelist_filename, 
        month = month,
        day = day,
        padding = padding,
        radius_miles = radius_miles,
        scoring_method = scoring_method)


    # Sort by scores
    #sorted_d = sorted(((value, key) for (key,value) in scores.items()), reverse=True)
    
    # Sort by number of targets
    sorted_d = sorted(((value, key) for (key,value) in scores.items()), reverse=True)

    if len(sorted_d) < num_spots:
        num_to_show = len(sorted_d)
    else:
        num_to_show = num_spots

    for i in range(num_to_show):
        center =  sorted_d[i][1]

        # Identify most common targets
        center_df = dfs[center]
        top_10percent = math.ceil(.1 * center_df.size)
        targets = list(center_df.reset_index()['index'][0:])

        print('Top spot {}:'.format(i+1), center)
        print('Number possible targets:', len(targets))
        print('Most common targets:', targets)
        print('')
    
    return scores

engine_path = "/Volumes/seagate-storage/db/ebird_small.db"
table_name = 'ebird_small_20190328'
lifelist_filename = 'tessa-lifelist.csv'
month = 3
day = 29
padding = 2
num_spots = 5
radius_miles = 100

tessa_scores_all = chaser(
    engine_path,
    table_name,
    lifelist_filename,
    month,
    day,
    padding,
    num_spots,
    radius_miles
)