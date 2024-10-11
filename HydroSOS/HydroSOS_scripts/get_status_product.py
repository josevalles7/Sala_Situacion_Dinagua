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
max_pct_missing = 50

values = ['High flow','Above normal','Normal range','Below normal','Low flow']
flow_cat = [5,4,3,2,1]

# ------------------------------------------------------------------------------
# Main functions
# ------------------------------------------------------------------------------
   
def monthly_status(DISCHARGE_MONTHLY):
    # Calculate long-term average
    DISCHARGE_SELECTION = DISCHARGE_MONTHLY[(DISCHARGE_MONTHLY['year'] >= stdStart) & (DISCHARGE_MONTHLY['year'] <= stdEnd)]
    DISCHARGE_AVERAGE = DISCHARGE_SELECTION.groupby(DISCHARGE_SELECTION.month).mean()
    DISCHARGE_AVERAGE = DISCHARGE_AVERAGE.reindex(columns=['mean_flow'])
    DISCHARGE_STATUS = DISCHARGE_MONTHLY.copy()
    # Calcular indicadores
    DISCHARGE_STATUS['percentile_flow'] = np.nan
    DISCHARGE_STATUS['rank_average'] = np.nan
    DISCHARGE_STATUS['complete%'] = np.nan

    for i in range(len(DISCHARGE_STATUS)):
        # Extract the current month 
        m = DISCHARGE_STATUS.month[i]
        # Extract the current year
        y = DISCHARGE_STATUS.year[i]
        DISCHARGE_STATUS.loc[DISCHARGE_STATUS.eval('month==@m & year==@y'),'rank_average']  = DISCHARGE_STATUS.query('month==@m')['mean_flow'].rank()
        DISCHARGE_STATUS.loc[DISCHARGE_STATUS.eval('month==@m & year==@y'),'complete%']  = DISCHARGE_STATUS.query('month==@m')["mean_flow"].notnull().sum()
        DISCHARGE_STATUS.loc[DISCHARGE_STATUS.eval('month==@m & year==@y'),'percentile_flow'] = (DISCHARGE_STATUS['mean_flow'][i] - DISCHARGE_AVERAGE.query('month == @m')["mean_flow"].item()) / DISCHARGE_AVERAGE.query('month == @m')["mean_flow"].item()

    DISCHARGE_STATUS['weibell_rank'] = DISCHARGE_STATUS['rank_average']/(DISCHARGE_STATUS['complete%']+1)

    criteria = [DISCHARGE_STATUS['weibell_rank'].between(percentile[3],1.00),
        DISCHARGE_STATUS['weibell_rank'].between(percentile[2],percentile[3]),
        DISCHARGE_STATUS['weibell_rank'].between(percentile[1],percentile[2]),
        DISCHARGE_STATUS['weibell_rank'].between(percentile[0],percentile[1]),
        DISCHARGE_STATUS['weibell_rank'].between(0.00,percentile[0])]

    DISCHARGE_STATUS['percentile_range'] = np.select(criteria,values,None)
    DISCHARGE_STATUS['flowcat'] = np.select(criteria,flow_cat,pd.NA)

    return DISCHARGE_STATUS

def quarterly_status(DISCHARGE_THREE_MONTHS):
    # # Calculate long-term average
    DISCHARGE_SELECTION_THREE_MONTH = DISCHARGE_THREE_MONTHS[(DISCHARGE_THREE_MONTHS['year'] >= stdStart) & (DISCHARGE_THREE_MONTHS['year'] < stdEnd)]
    DISCHARGE_AVERAGE_THREE_MONTH = DISCHARGE_SELECTION_THREE_MONTH.groupby(DISCHARGE_SELECTION_THREE_MONTH.startMonth).mean()
    DISCHARGE_AVERAGE_THREE_MONTH = DISCHARGE_AVERAGE_THREE_MONTH.reindex(columns=['mean_flow'])
    DISCHARGE_QUATERLY = DISCHARGE_THREE_MONTHS.copy()
    # Calcular indicadores
    DISCHARGE_QUATERLY['percentage_flow'] = np.nan
    DISCHARGE_QUATERLY['rank_average'] = np.nan
    DISCHARGE_QUATERLY['complete%'] = np.nan

    for i in range(len(DISCHARGE_QUATERLY)):
        # Extract the current month 
        m = DISCHARGE_QUATERLY.startMonth[i]
        # Extract the current year
        y = DISCHARGE_QUATERLY.year[i]
        DISCHARGE_QUATERLY.loc[DISCHARGE_QUATERLY.eval('startMonth==@m & year==@y'),'rank_average']  = DISCHARGE_QUATERLY.query('startMonth==@m')['mean_flow'].rank()
        DISCHARGE_QUATERLY.loc[DISCHARGE_QUATERLY.eval('startMonth==@m & year==@y'),'complete%']  = DISCHARGE_QUATERLY.query('startMonth==@m')["mean_flow"].notnull().sum()
        DISCHARGE_QUATERLY.loc[DISCHARGE_QUATERLY.eval('startMonth==@m & year==@y'),'percentage_flow'] = (DISCHARGE_QUATERLY['mean_flow'][i] - DISCHARGE_AVERAGE_THREE_MONTH.query('startMonth == @m')["mean_flow"].item()) / DISCHARGE_AVERAGE_THREE_MONTH.query('startMonth == @m')["mean_flow"].item()

    DISCHARGE_QUATERLY['weibell_rank'] = DISCHARGE_QUATERLY['rank_average']/(DISCHARGE_QUATERLY['complete%']+1)
   
    criteria_three_months = [DISCHARGE_QUATERLY['weibell_rank'].between(percentile[3],1.00),
        DISCHARGE_QUATERLY['weibell_rank'].between(percentile[2],percentile[3]),
        DISCHARGE_QUATERLY['weibell_rank'].between(percentile[1],percentile[2]),
        DISCHARGE_QUATERLY['weibell_rank'].between(percentile[0],percentile[1]),
        DISCHARGE_QUATERLY['weibell_rank'].between(0.00,percentile[0])]

    DISCHARGE_QUATERLY['percentile_range'] = np.select(criteria_three_months,values,None)
    DISCHARGE_QUATERLY['flowcat'] = np.select(criteria_three_months,flow_cat,pd.NA)

    row_labels = {1:'JFM',
            2:'FMA',
            3:'MAM',
            4:'AMJ',
            5:'MJJ',
            6:'JJA',
            7:'JAS',
            8:'ASO',
            9:'SON',
            10:'OND',
            11:'NDE',
            12:'DEF'}
    
    DISCHARGE_QUATERLY['period'] = DISCHARGE_QUATERLY['startMonth'].replace(row_labels) 
    return DISCHARGE_QUATERLY

def annualy_status(DISCHARGE_TWELVE_MONTHS):
    DISCHARGE_SELECTION_TWELVE_MONTH = DISCHARGE_TWELVE_MONTHS[(DISCHARGE_TWELVE_MONTHS['year'] >= stdStart) & (DISCHARGE_TWELVE_MONTHS['year'] < stdEnd)]
    DISCHARGE_AVERAGE_TWELVE_MONTH = DISCHARGE_SELECTION_TWELVE_MONTH.groupby(DISCHARGE_SELECTION_TWELVE_MONTH.startMonth).mean()
    DISCHARGE_AVERAGE_TWELVE_MONTH = DISCHARGE_AVERAGE_TWELVE_MONTH.reindex(columns=['mean_flow'])
    DISCHARGE_ANNUALY = DISCHARGE_TWELVE_MONTHS.copy()
    # Calcular indice
    DISCHARGE_ANNUALY['percentage_flow'] = np.nan
    DISCHARGE_ANNUALY['rank_average'] = np.nan
    DISCHARGE_ANNUALY['complete%'] = np.nan

    for i in range(len(DISCHARGE_ANNUALY)):
        # Extract the current month 
        m = DISCHARGE_ANNUALY.startMonth[i]
        # Extract the current year
        y = DISCHARGE_ANNUALY.year[i]
        DISCHARGE_ANNUALY.loc[DISCHARGE_ANNUALY.eval('startMonth==@m & year==@y'),'rank_average']  = DISCHARGE_ANNUALY.query('startMonth==@m')['mean_flow'].rank()
        DISCHARGE_ANNUALY.loc[DISCHARGE_ANNUALY.eval('startMonth==@m & year==@y'),'complete%']  = DISCHARGE_ANNUALY.query('startMonth==@m')["mean_flow"].notnull().sum()
        DISCHARGE_ANNUALY.loc[DISCHARGE_ANNUALY.eval('startMonth==@m & year==@y'),'percentage_flow'] = (DISCHARGE_ANNUALY['mean_flow'][i] - DISCHARGE_AVERAGE_TWELVE_MONTH.query('startMonth == @m')["mean_flow"].item()) / DISCHARGE_AVERAGE_TWELVE_MONTH.query('startMonth == @m')["mean_flow"].item()

    DISCHARGE_ANNUALY['weibull_rank'] = DISCHARGE_ANNUALY['rank_average']/(DISCHARGE_ANNUALY['complete%']+1)
    
    criteria_twelve_months = [DISCHARGE_ANNUALY['weibull_rank'].between(percentile[3], 1.00),
                          DISCHARGE_ANNUALY['weibull_rank'].between(percentile[2], percentile[3]),
                          DISCHARGE_ANNUALY['weibull_rank'].between(percentile[1], percentile[2]),
                          DISCHARGE_ANNUALY['weibull_rank'].between(percentile[0], percentile[1]),
                          DISCHARGE_ANNUALY['weibull_rank'].between(0.00, percentile[0])]
        
    DISCHARGE_ANNUALY['percentile_range'] = np.select(criteria_twelve_months,values,None)
    DISCHARGE_ANNUALY['flowcat'] = np.select(criteria_twelve_months,flow_cat,pd.NA)

    return DISCHARGE_ANNUALY

def export_csv(groupBy,output_directory,filename):
    groupBy['date'] = pd.to_datetime(groupBy[['year', 'month']].assign(DAY=1))
    groupBy['date'] = groupBy['date'].dt.strftime('%Y-%m-%d')
    groupBy['flowcat'] = groupBy['flowcat'].astype('Int64')
    groupBy.sort_values(['year','month']).filter(['date','flowcat']).to_csv(f"{output_directory}cat_{filename}.csv", index=False)
    print('CSV FILE GENERATED')

def csv_to_json(input_csv,outpu_json):
    allFilesDF = pd.DataFrame()
    # read the CSV files in the data directory
    for index, filename in enumerate(os.listdir(input_csv)):
            with open(input_csv+'/'+filename, mode="r") as fr:
                if filename.endswith('.csv'):
                    df = pd.read_csv(fr)
                    filename = os.path.splitext(str(filename))[0] #remove file extenstion
                    stationID = filename.split('_')[1] #remove cat_
                    df['stationID'] = stationID
                    allFilesDF = pd.concat([allFilesDF,df])

    allFilesDF['date'] = pd.to_datetime(allFilesDF['date'])
    allFilesDF = allFilesDF.sort_values(by='date', ascending=True)
    allFilesDF.drop_duplicates(inplace=True)
    allFilesDF.set_index(['date'], inplace=True)
    allFilesDF.rename(columns={"flowcat":"category"}, inplace=True)
    allFilesDF['category'] = allFilesDF['category'].astype('Int64')

    for date in allFilesDF.index:
        #this happens if there is only one record
        if type(allFilesDF.loc[date]) == pd.core.series.Series:
            pd.DataFrame(allFilesDF.loc[date]).T.to_json(f"{outpu_json}/{date.strftime('%Y-%m')}.json", orient = 'records')
        else: 
            allFilesDF.loc[date].to_json(f"{outpu_json}/{date.strftime('%Y-%m')}.json", orient = 'records')

    print('JSON FILE GENERATED')