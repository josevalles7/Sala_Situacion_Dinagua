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

def import_data(input_directory, filename):
    flowdata = pd.read_csv(f"{input_directory}{filename}", parse_dates=['Fecha'],
                           index_col="Fecha", dayfirst=True, na_values="NA")
    full_range = pd.date_range(start=flowdata.index[0], end=flowdata.index[-1], freq='D')
    flowdata = flowdata.reindex(full_range).rename_axis("date")
    flowdata.columns = ['flow']
    station = filename.split('.')[0]

    flowdata['month'] = flowdata.index.month
    flowdata['year'] = flowdata.index.year
    flowdata = flowdata.reset_index()

    n_missing = flowdata['flow'].isnull().sum()
    print(station)
    print(f"There are {flowdata['year'].max() - flowdata['year'].min()} years of data in this file.")
    print(f"There are {n_missing} missing data points, which is {np.round(n_missing / len(flowdata) * 100, 2)}% of the total data")
    return flowdata, station

def calculate_monthly(flowdata):
    flowdata = flowdata.set_index('date')
    resampled = flowdata['flow'].resample('ME')
    monthly_mean = resampled.mean()
    monthly_count = resampled.count()
    monthly_size = resampled.size()
    pct_missing = (1 - monthly_count / monthly_size) * 100
    monthly_mean[pct_missing >= max_pct_missing] = np.nan

    result = pd.DataFrame({'mean_flow': monthly_mean})
    result['month'] = result.index.month
    result['year'] = result.index.year
    result = result.reset_index()[['date', 'month', 'year', 'mean_flow']]
    return result

def import_monthly(input_directory, filename):
    station = filename.split('.')[0]
    df = pd.read_csv(f"{input_directory}{filename}", parse_dates=['Fecha'],
                     index_col="Fecha", dayfirst=True, na_values="NA")
    df.columns = ['mean_flow']
    df.index = df.index.to_period('M').to_timestamp()
    df = df.rename_axis("date")
    df['year'] = df.index.year
    df['month'] = df.index.month
    df = df.reset_index()[['date', 'month', 'year', 'mean_flow']]
    return df, station

def calculate_accumulated(DISCHARGE_MONTHLY, scale):
    df = DISCHARGE_MONTHLY.set_index('date') if 'date' in DISCHARGE_MONTHLY.columns else DISCHARGE_MONTHLY.copy()
    series = df['mean_flow']

    min_periods = int(np.ceil(scale * (1 - max_pct_missing / 100) + 1e-9))
    rolling_mean = series.rolling(scale, min_periods=min_periods).mean()
    rolling_count = series.rolling(scale, min_periods=1).count()
    rolling_mean[rolling_count < min_periods] = np.nan

    result = pd.DataFrame({'mean_flow': rolling_mean})
    result['startMonth'] = (result.index - pd.DateOffset(months=(scale - 1))).month
    result['endMonth'] = result.index.month
    result['month'] = result.index.month
    result['year'] = result.index.year
    result.index = result.index.to_period('M').to_timestamp()
    result = result.rename_axis('date').reset_index()
    return result[['date', 'startMonth', 'endMonth', 'month', 'year', 'mean_flow']]

    