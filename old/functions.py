import csv
import pandas as pd
import numpy as np
from vincenty import vincenty
import datetime
import collections


def show_unique(series):
    '''
    Return a list of the unique elements in a pandas series
    '''
    
    all_elements = list(series)
    seen = set()
    seen_add = seen.add
    unique_elements = [x for x in all_elements if not (x in seen or seen_add(x))]

    return unique_elements

def remove_subspp(string):
    '''
    Common names sometimes have a parenthetical comment
    about supspecific designation at the end of the 
    species name. Returns the first part of the name
    before the open parenthesis (with ' ' stripped off)
    '''
    return string.split('(')[0].strip()


def identify_centers(df, radius_miles = 5):
    '''
    Create a dictionary where the
    keys = centers and the values = list of points
    within the desired radius
    '''
    
    # Create a list of all unique points to use for our centers
    all_points = show_unique(df['Location'])
    centers = all_points #TODO: create a more efficient center-finding algo

    my_dict = {}
    centers = all_points
    for center in centers:
        close_points = []
        for point in all_points:
            distance = vincenty(center, point, miles=True)
            if distance < radius_miles:
                close_points.append(point)

        my_dict[center] = close_points
        
    return my_dict




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
    
    delta = date1-date2
    way1 = delta.days % 365
    way2 = 365-way1
    
    if way1 < way2: return way1
    else: return way2


    
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
    return df[df['Location'].isin(my_dict[center])]
    

def select_date_df(df, year, month, day, interval=4): 
    '''
    Select relevant sightings by date
    
    For a single center (key), return a DF with only sightings from a desired date range
    
    Inputs:
        df: the full dataframe to select sightings from
        year, month, day: the date to center a date range around
        interval: the number of days before & after the specified
            date to include sightings from
    
    '''
    
    # Select only locations within date range
    desired_date=datetime.date(year, month, day)
    center_sightings['Interval'] = center_sightings['Date'].apply(interval_without_year, date2=desired_date)
    selected_sightings = center_sightings.loc[center_sightings['Interval'] <= interval]
    
     
    return selected_sightings

    
    
def calculate_score(df):

    '''
    Calculate score of DF
    
    Calculate the score of a DF by finding
    the number of checklists on which a species was reported.
    This could be modified to be more sophisticated in the future.
    
    Inputs:
        df: a dataframe with a column 'Common Name'
    
    Outputs:
        the sum of the number of checklists each species
        appeared on--which is identical to df.shape[0]
    '''
    
    
    #sum(df['Common Name'].value_counts) # Means the same thing as below
    
    return df.shape[0]

    
    
def import_data(data_filename, lifelist_filename, year, month, day):

    '''
    
    Superfunction to import and select relevant data
    
    Returns:
        A dictionary where the keys are centers, and the
        values are dataframes. Each dataframe contains
        sightings of lifer birds from the desired day 
        range within the radius of the key
    '''
    
    # Import data
    rough_df = pd.DataFrame.from_csv(data_filename, index_col=None)

    # Add location column
    rough_df['Location'] = rough_df.apply(lambda row: (row['Latitude'], row['Longitude']), axis=1)
    
    # Remove "sp.," slashes, and hybrids through a several-step process:
    rough_df = rough_df.loc[
        ~(
            rough_df['Scientific Name'].str.contains('\.')
        ) &
        ~(
            (
                rough_df['Scientific Name'].str.contains('/')
            ) & 
            (
                ~rough_df['Common Name'].str.contains('\(') 
                # Required because some subspecific designations (i.e. those with
                # parentheses in the common name) have slashes in the scientific name
                # (and in the common name!)
                # This isn't perfect because of Traill's and Western species groups
                # (and potentially some others), which is taken care of later.
            )
        ) &
        ~(
            rough_df['Common Name'].str.contains('hybrid')
        )
    ]
    # Remove subspecific designations
    rough_df['Common Name'] = rough_df['Common Name'].apply(remove_subspp)
    # Remove those pesky species slashes like Pac-Slope/Cordy (Western)
    rough_df = rough_df.loc[~rough_df['Common Name'].str.contains('/')]

    # Select the necessary columns
    fine_df = rough_df[['Submission ID', 'Common Name', 'Count', 'Location', 'Date']]
    
    # Replace Xs with NaNs
    fine_df.reset_index(drop=True, inplace=True) # Drop current index (don't incorporate into DF)
    df = fine_df.replace(to_replace='X', value=1)
    df['Count'] = pd.to_numeric(df['Count']) #Coerce 1s from strs to numeric
    df['Date'] = pd.to_datetime(df['Date']).dt.date # Convert to datetime.date
    
    # Generate list of lifers from .csv file
    with open(lifelist_filename) as f:
        reader = csv.reader(f)
        for line in reader:
            life_list.append(line[0].lower()) 

    # Remove species that are already on one's life list
    df = df[~df['Common Name'].str.lower().isin(life_list)]
    
    
    # Remove checklists from outside of this date range
    df = select_date_df(df, year, month, day, interval=4)
    
    
    # Identify a dict of centers
    my_dict = identify_centers(df, radius_miles = 5)
    
    
    # For each center, generate a relevant DF and calculate its score
    all_dfs = {}
    all_scores = {}
    for center in my_dict.keys():
        
        # Select only locations within radius
        selected_df = select_loc_df(df, my_dict, center)
        
        # Calculate score
        score = calculate_score(selected_df)
        
        all_dfs[center] = selected_df
        all_scores[center] = score
        
    
    return all_dfs, all_scores




def main(data_filename, lifelist_filename, year, month, day):
    
    # Get dict of dfs of all lifer sightings
    dfs, scores = import_data(data_filename, lifelist_filename, year, month, day)
    
    # Score each sighting 
    print(scores)
    
    



