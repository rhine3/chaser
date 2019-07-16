'''
chaser.py
Tessa Rhinehart

Functions to analyze eBird frequency table .csvs
Frequency table .csvs are obtainable through rebird 
(https://github.com/ropensci/rebird) function ebirdfreq()
'''

import os
import pandas as pd

########## HELPER FUNCTIONS ##########

def show_unique(series):
    '''
    Return a list of the unique
    elements in a series
    '''
    
    all_elements = list(series)
    seen = set()
    seen_add = seen.add
    unique_elements = [x for x in all_elements if not (x in seen or seen_add(x))]

    return unique_elements

def load_freq_csv(path):
    '''
    Loads a frequency csv
    
    Loads a frequency csv generated by rebird
    function ebirdfreq()
    
    Inputs:
        path (string): path to csv
    
    Returns:
        loaded dataframe
    '''
    
    return pd.read_csv(path, index_col='Unnamed: 0')

def load_life_list(path):
    '''
    Load a life list
    
    Create a dataframe from a .csv of a life list
    
    Inputs:
        path: path to life list csv, where csv contains
            a column "Species" with values equal to a 
            common name and a scientific name separated 
            by a hyphen surrounded by spaces, e.g.
            'Chestnut-sided Warbler - Setophaga pensylvanica'
    
    Returns:
        a dataframe with the columns of the original 
        csv, plus new columns for common name only and scientific
        name only
    '''
    
    life_data = pd.read_csv(path)

    # Break "Species" column into two columns, splitting on a hyphen with two spaces around it
    life_data[['Common Name', 'Scientific Name']] = life_data.Species.str.split(' - ', expand=True) 
    
    return life_data


########## COUNTY ANALYSIS PIPELINE ##########

def analyze_county(freq_path, life_list_path, desired_weeks, freq_thresh):
    '''
    Find lifers with desired parameters
    
    Inputs:
        freq_path (string): path to csv generated by rebird's
            ebirdfreq() function
        life_list_path (string): path to life list csv, where csv contains
            a column "Species" with values equal to a 
            common name and a scientific name separated 
            by a hyphen surrounded by spaces, e.g.
            'Chestnut-sided Warbler - Setophaga pensylvanica'
        weeks (list): list of strings of desired weeks, where
            each string is of the format "Month-X", where
            "Month" is a capitalized full month name, and X
            is an integer, 1-4, representing the week of the
            month that is desired
        freq_thresh (float): percentage threshold (0-1) below
            which species frequencies should be excluded
    '''
    
    # Load data
    raw_freqs = load_freq_csv(freq_path)
    raw_lifelist = load_life_list(life_list_path)
    lifelist = list(raw_lifelist['Common Name'])
    
    # Perform analyses
    analyzed = select_weeks(weeks = desired_weeks, df = raw_freqs)
    analyzed = remove_spuhs(df = analyzed)
    analyzed = keep_lifers(life_list = lifelist, df = analyzed)
    analyzed = average_freqs(df = analyzed)
    analyzed = threshold_freqs(df = analyzed, thresh = freq_thresh)
    
    # Sort in descending order of frequency and reindex
    analyzed = analyzed.sort_values(
        by = 'frequency', ascending = False).reset_index(drop=True)
    
    return analyzed

    

########## SINGLE COUNTY ANALYSIS FUNCTIONS ##########

def select_weeks(weeks, df):
    '''
    Selects rows from frequency df from desired weeks
    
    Inputs:
        weeks (list): list of strings of desired weeks, where
            each string is of the format "Month-X", where
            "Month" is a capitalized full month name, and X
            is an integer, 1-4, representing the week of the
            month that is desired
        df (pandas DataFrame): dataframe with a column 'monthQt'
            with weeks in the format described above
    
    Returns: 
        df containing only rows that have 'monthQt' matching
        the desired week.
    '''

    return df[df['monthQt'].isin(weeks)]


def remove_spuhs(df):
    '''
    Remove rows for non-species
    
    Remove non-species rows in dataframe,
    i.e. rows for "spuhs" and "slashes "(observations not 
    identified completely to species), and hybrids
    '''
    
    return df.loc[
        # Remove anything that contains a dot (i.e. a "spuh")
        ~(
            df['comName'].str.contains('\.')
        ) &
        # Remove anything that contains a forward slash (i.e. an uncertain ID)
        ~(
            df['comName'].str.contains('/')
        ) &
        # Remove anything that is a hybrid
        ~(
            df['comName'].str.contains('hybrid')
        )
    ]

def keep_lifers(life_list, df):
    '''
    Remove non-lifers from df
    
    Inputs:
        life_list (list): a list of string species names
            to remove from df
        df (pandas DataFrame): a dataframe with a column 'comName'
            containing species common names
            
    Returns:
        df, without rows where 'comName' value was in life_list
    '''
    
    return df[~ df['comName'].isin(life_list)]

def average_freqs(df):
    '''
    Average frequencies across multiple weeks
    
    For each species, average all frequency estimates in one
    week and collapse estimates into a single row.
    
    Inputs:
        df (pandas DataFrame): a dataframe of frequency
            records with columns 'comName' and 'frequency'
    
    Returns:
        DataFrame with average frequency estimates for each species
    '''
    
    averaged_freqs = pd.DataFrame({'comName':[], 'frequency':[]})
    species = show_unique(df['comName'])
    for idx, sp in enumerate(species):
        freq = df[
            df['comName'] == sp]['frequency'].mean()
        averaged_freqs.loc[idx] = {'comName':sp, 'frequency':freq}
    
    return averaged_freqs

def threshold_freqs(df, thresh):
    '''
    Remove species with low frequency
    
    Remove species where frequency of occurrence
    falls below a desired level. This function's intended
    use is for DataFrames with one row for each species, 
    containing a 'frequency' column corresponding
    to average frequency of the species. 
    
    It is possible to use the function for non-average
    frequencies, but these results should (obviously) not be 
    used to generate averaged frequency estimates
    
    Inputs:
        df (pandas DataFrame): dataframe as described above
            with float 'frequency' column
        thresh (float): threshold below which to remove species.
            Should be a percentage from 0 to 1. 
    
    Returns: 
        dataframe with low-frequency species removed
    '''

    return df[df['frequency'] >= thresh]