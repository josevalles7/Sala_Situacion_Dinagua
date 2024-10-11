"""
Functions for transforming daily to monthly discharge
Based on STATUSCALCV2.R by Katie Facer-Childs and Ezra Kitson
@author: Jose Valles (09/11/2023)
DINAGUA - URUGUAY
"""
import pandas as pd
import numpy as np

# ------------------------------------------------------------------------------
# Parameters
# ------------------------------------------------------------------------------

max_pct_missing = 50

# ------------------------------------------------------------------------------
# Main functions
# ------------------------------------------------------------------------------

def import_data(input_directory,filename):
    
    flowdata = pd.read_csv(f"{input_directory}{filename}",parse_dates=['Fecha'],index_col="Fecha",dayfirst=True,na_values="NA")
    diff = pd.date_range(start = flowdata.index[0].strftime('%Y-%m-%d'), end = flowdata.index[-1].strftime('%Y-%m-%d'),freq='D')
    # Re-index the dataframe based on the missind date variable
    flowdata = flowdata.reindex(diff,fill_value=None)
    # Set index Fecha
    flowdata.index.name = 'Fecha'
    flowdata = flowdata.rename_axis("date")
    # Change columns names
    flowdata.columns = ['flow']
    station = filename.split('.')[0]

    #month and year column
    flowdata['month'] = flowdata.index.month
    flowdata['year'] = flowdata.index.year
    flowdata = flowdata.reset_index()

    #check whether or not there is enough data? 
    print(station)
    print(f"There are {flowdata['year'].max() - flowdata['year'].min()} years of data in this file.")
    print(f"There are {sum(flowdata['flow'].isnull())} missing data points, which is {np.round(sum(flowdata['flow'].isnull())/len(flowdata) * 100,2)}% of the total data")
    return flowdata, station

def calculate_monthly(flowdata):
    # Set index of the input data
    flowdata.set_index('date', inplace=True)
    # define a missing formula function
    def calculate_missing_percentage(x):
        pct_missing = x.isnull().sum() * 100 / len(x)
        return round(pct_missing,2)
    # Aggregate data daily to monthly and calculate when the missing values are below max_pct_missing
    DISCHARGE_MONTHLY = flowdata.resample('M',closed="right").apply(
        lambda x: x.mean() if calculate_missing_percentage(x) < max_pct_missing else np.nan
        )
    # create columns
    DISCHARGE_MONTHLY['year'] = DISCHARGE_MONTHLY.index.year
    DISCHARGE_MONTHLY['month'] = DISCHARGE_MONTHLY.index.month
    # reset index
    DISCHARGE_MONTHLY.reset_index(inplace=True)
    # rename and reorder columns
    DISCHARGE_MONTHLY.rename(columns={'flow':'mean_flow'}, inplace=True)
    new_order = ['date', 'month', 'year', 'mean_flow']
    DISCHARGE_MONTHLY = DISCHARGE_MONTHLY[new_order]
    # output
    return DISCHARGE_MONTHLY

def import_monthly(input_directory,filename):
        station = filename.split('.')[0]
        DISCHARGE_MONTHLY = pd.read_csv(f"{input_directory}{filename}",parse_dates=['Fecha'],index_col="Fecha",dayfirst=True,na_values="NA")
        DISCHARGE_MONTHLY.columns = ['mean_flow']
        DISCHARGE_MONTHLY.index.name = 'date'
        DISCHARGE_MONTHLY['year'] = DISCHARGE_MONTHLY.index.year
        DISCHARGE_MONTHLY['month'] = DISCHARGE_MONTHLY.index.month
        DISCHARGE_MONTHLY = DISCHARGE_MONTHLY.rename_axis("date")
        DISCHARGE_MONTHLY.index = DISCHARGE_MONTHLY.index.map(lambda t: t.replace(day=1))
        DISCHARGE_MONTHLY = DISCHARGE_MONTHLY.reset_index()
        new_order = ['date','month', 'year', 'mean_flow']
        DISCHARGE_MONTHLY = DISCHARGE_MONTHLY[new_order]
        return DISCHARGE_MONTHLY, station

def calculate_accumulated(DISCHARGE_MONTHLY,scale):
    DISCHARGE_MONTHLY = DISCHARGE_MONTHLY.reset_index()
    # Set index of the input data
    DISCHARGE_MONTHLY.set_index('date', inplace=True)
    # define a missing formula function
    def calculate_missing_percentage(x):
        pct_missing = x.isnull().sum() * 100 / len(x)
        return round(pct_missing,2)
    
    # Aggregate data daily to monthly and calculate when the missing values are below max_pct_missing
    # DISCHARGE_MONTHLY = flowdata.resample('M',closed="right").apply(
    #     lambda x: x.mean() if calculate_missing_percentage(x) < max_pct_missing else np.nan
    #     )
    # Drop columns that are not necessary
    DISCHARGE_MONTHLY.drop(columns=['month','year'])
    # Calculate the multimonthly (scale) mean of discharge if the missing values are below the max_pct_missing
    DISCHARGE_AGGREGATE = pd.DataFrame(DISCHARGE_MONTHLY['mean_flow'].rolling(scale).apply(
        lambda x: x.mean() if calculate_missing_percentage(x) < max_pct_missing else np.nan
        ))
    # Create columns 
    DISCHARGE_AGGREGATE['startMonth'] = (DISCHARGE_AGGREGATE.index - pd.DateOffset(months=(scale-1))).month
    DISCHARGE_AGGREGATE['endMonth'] = DISCHARGE_AGGREGATE.index.month
    DISCHARGE_AGGREGATE['month'] = DISCHARGE_AGGREGATE.index.month
    DISCHARGE_AGGREGATE['year'] = DISCHARGE_AGGREGATE.index.year
    DISCHARGE_AGGREGATE.index = DISCHARGE_AGGREGATE.index.map(lambda t: t.replace(day=1))
    DISCHARGE_AGGREGATE.reset_index(inplace=True)
    # Rename and reorder columns
    # DISCHARGE_AGGREGATE.rename(columns={'flow':'mean_flow'}, inplace=True)
    new_order = ['date','startMonth', 'endMonth', 'month','year', 'mean_flow']
    DISCHARGE_AGGREGATE = DISCHARGE_AGGREGATE[new_order]
    # Output
    return DISCHARGE_AGGREGATE

    