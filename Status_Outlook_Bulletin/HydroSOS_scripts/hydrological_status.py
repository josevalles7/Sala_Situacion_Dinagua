"""
Functions for HydroSOS Status product
Based on STATUSCALCV2.R by Katie Facer-Childs and Ezra Kitson
@author: Jose Valles (09/11/2023)
DINAGUA - URUGUAY
"""
import pandas as pd
import numpy as np
import os

# ------------------------------------------------------------------------------
# Hydrological Status Parameters
# ------------------------------------------------------------------------------

stdStart = 1981
stdEnd = 2010
percentile = [0.10, 0.25, 0.75, 0.90]

values = ['High flow','Above normal','Normal range','Below normal','Low flow']
flow_cat = [5,4,3,2,1]

# ------------------------------------------------------------------------------
# Define plotting position parameters
# Cunnane is alphap = 0.4 and betap = 0.4 
# Weibull is alphap = 0 and betap = 0 
# ------------------------------------------------------------------------------
alphap = 0.4
betap = 0.4

# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def _classify(df):
    wr = df['pct_rank']
    criteria = [
        (wr >= percentile[3]) & (wr <= 1.00),
        (wr > percentile[2]) & (wr < percentile[3]),
        (wr >= percentile[1]) & (wr <= percentile[2]),
        (wr >= percentile[0]) & (wr < percentile[1]),
        (wr >= 0.00) & (wr < percentile[0]),
    ]
    df['percentile_range'] = np.select(criteria, values, None)
    df['flowcat'] = np.select(criteria, flow_cat, pd.NA)

def _compute_status(df, group_col, avg_series, anomaly_col,alphap,betap):
    avg_map = df[group_col].map(avg_series)
    df[anomaly_col] = (df['mean_flow'] - avg_map) / avg_map
    df['rank_average'] = df.groupby(group_col)['mean_flow'].rank()
    df['complete%'] = df.groupby(group_col)['mean_flow'].transform(lambda x: x.notnull().sum())
    df['pct_rank'] = (df['rank_average'] - alphap) / (df['complete%'] + 1 - alphap - betap)
    _classify(df)

# ------------------------------------------------------------------------------
# Main functions
# ------------------------------------------------------------------------------

def monthly_status(DISCHARGE_MONTHLY):
    avg = DISCHARGE_MONTHLY[
        (DISCHARGE_MONTHLY['year'] >= stdStart) & (DISCHARGE_MONTHLY['year'] <= stdEnd)
    ].groupby('month')['mean_flow'].mean()

    df = DISCHARGE_MONTHLY.copy()
    _compute_status(df, 'month', avg, 'percentile_flow', alphap=alphap, betap=betap)
    return df

def quarterly_status(DISCHARGE_THREE_MONTHS):
    avg = DISCHARGE_THREE_MONTHS[
        (DISCHARGE_THREE_MONTHS['year'] >= stdStart) & (DISCHARGE_THREE_MONTHS['year'] < stdEnd)
    ].groupby('startMonth')['mean_flow'].mean()

    df = DISCHARGE_THREE_MONTHS.copy()
    _compute_status(df, 'startMonth', avg, 'percentage_flow', alphap=alphap, betap=betap)

    row_labels = {1:'EFM', 2:'FMA', 3:'MAM', 4:'AMJ', 5:'MJJ', 6:'JJA',
                  7:'JAS', 8:'ASO', 9:'SON', 10:'OND', 11:'NDE', 12:'DEF'}
    df['period'] = df['startMonth'].replace(row_labels)
    return df

def bimonthly_status(DISCHARGE_TWO_MONTHS):
    avg = DISCHARGE_TWO_MONTHS[
        (DISCHARGE_TWO_MONTHS['year'] >= stdStart) & (DISCHARGE_TWO_MONTHS['year'] < stdEnd)
    ].groupby('startMonth')['mean_flow'].mean()

    df = DISCHARGE_TWO_MONTHS.copy()
    _compute_status(df, 'startMonth', avg, 'percentage_flow', alphap=alphap, betap=betap)

    row_labels = {1:'EF', 2:'FM', 3:'MA', 4:'AM', 5:'MJ', 6:'JJ',
                  7:'JA', 8:'AS', 9:'SO', 10:'ON', 11:'ND', 12:'DE'}
    df['period'] = df['startMonth'].replace(row_labels)
    return df

def semiannual_status(DISCHARGE_SIX_MONTHS):
    avg = DISCHARGE_SIX_MONTHS[
        (DISCHARGE_SIX_MONTHS['year'] >= stdStart) & (DISCHARGE_SIX_MONTHS['year'] < stdEnd)
    ].groupby('startMonth')['mean_flow'].mean()

    df = DISCHARGE_SIX_MONTHS.copy()
    _compute_status(df, 'startMonth', avg, 'percentage_flow', alphap=alphap, betap=betap)

    row_labels = {1:'JFMAMJ', 2:'FMAMJJ', 3:'MAMJJA', 4:'AMJJAS', 5:'MJJASO', 6:'JJASON',
                  7:'JASOND', 8:'ASONJF', 9:'SONDJF', 10:'ONDJFM', 11:'NDJFMA', 12:'DJFMAM'}
    df['period'] = df['startMonth'].replace(row_labels)
    return df

def annualy_status(DISCHARGE_TWELVE_MONTHS):
    avg = DISCHARGE_TWELVE_MONTHS[
        (DISCHARGE_TWELVE_MONTHS['year'] >= stdStart) & (DISCHARGE_TWELVE_MONTHS['year'] < stdEnd)
    ].groupby('startMonth')['mean_flow'].mean()

    df = DISCHARGE_TWELVE_MONTHS.copy()
    _compute_status(df, 'startMonth', avg, 'percentage_flow', alphap=alphap, betap=betap)
    return df

def export_csv(groupBy, output_directory, filename):
    groupBy['date'] = pd.to_datetime(groupBy[['year', 'month']].assign(DAY=1))
    groupBy['date'] = groupBy['date'].dt.strftime('%Y-%m-%d')
    groupBy['flowcat'] = groupBy['flowcat'].astype('Int64')
    groupBy.sort_values(['year','month']).filter(['date','flowcat']).to_csv(f"{output_directory}cat_{filename}.csv", index=False)
    print('CSV FILE GENERATED')

def csv_to_json(input_csv, outpu_json):
    dfs = []
    for filename in os.listdir(input_csv):
        if not filename.endswith('.csv'):
            continue
        df = pd.read_csv(os.path.join(input_csv, filename))
        station_id = os.path.splitext(filename)[0].split('_')[1]
        df['stationID'] = station_id
        dfs.append(df)

    allFilesDF = pd.concat(dfs, ignore_index=True)
    allFilesDF['date'] = pd.to_datetime(allFilesDF['date'])
    allFilesDF = allFilesDF.sort_values(by='date').drop_duplicates()
    allFilesDF.rename(columns={"flowcat": "category"}, inplace=True)
    allFilesDF['category'] = allFilesDF['category'].astype('Int64')
    allFilesDF.set_index('date', inplace=True)

    for date, group in allFilesDF.groupby(level=0):
        group.reset_index(drop=True).to_json(
            f"{outpu_json}/{date.strftime('%Y-%m')}.json", orient='records'
        )

    print('JSON FILE GENERATED')