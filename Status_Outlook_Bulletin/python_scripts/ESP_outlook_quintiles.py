# %% [markdown]
# # Pronostico basado en ESP para toda las cuencas

# %% [markdown]
# Este notebook realiza el pronosticos hidrologico sub-estacional a estacional (S2S) en todas las cuencas. Brinda como resultado archivos CSV para ser utilizado en GIS y hacer el mapa de visualización de pronosticos para todas las cuencas nivel 2

# %%
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use('classic')
import numpy as np
import calendar
from datetime import datetime, timedelta
import argparse

# Define arguments 
parser = argparse.ArgumentParser(
                    prog='ESP_outlook_quintiles',
                    description='Postprocess the ESP outlook products',
                    epilog='Jose Valles, DINAGUA, 08Nov2024')

# 
parser.add_argument('forecast_leadtime', help='provide forecast leadtime')
parser.add_argument('end_date', help='end date for the discharge plot in format YYYY-MM-DD')

args = parser.parse_args()

# Calculate start date as one year before the provided end date
end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
start_date = end_date - timedelta(days=365)  # Subtracting 365 days for a year difference

# Format dates as strings
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# %%
allbasins_n2 = pd.read_csv(f'../balance_hidrico_regional/output_modelo/cuenca_nivel2.csv',index_col="Codigo")

# %% [markdown]
# Importar codigos de cuenca nivel 2 y 3

# %%
def importmodelensemble(codcuenca_n2):
    basin_level3 = pd.read_csv(f'../balance_hidrico_regional/output_modelo/cuenca_nivel3.csv',usecols=lambda col: col.startswith(str(codcuenca_n2)))
    basin_level2 = pd.read_csv(f'../balance_hidrico_regional/output_modelo/cuenca_nivel2.csv',usecols=lambda col: col.startswith(str(codcuenca_n2)))
    # Insert the folder path 
    folder_path = '../balance_hidrico_regional/output_modelo/esp/'
    # get a list of all CSV file in the folder
    file_list = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
    # Initialize an empty list to store dataframes
    df_list = []

    # Iterate over the list of files and read each one into a dataframe
    for file in file_list:
        # Importar los datos 
        file_path = os.path.join(folder_path,file)
        df = pd.read_csv(file_path,usecols=lambda col: col.startswith((str(codcuenca_n2),'-1')))
        df = df.rename(columns={'-1': 'year','-1.1':'month'})
        df['date'] = pd.to_datetime(dict(year=df['year'],month=df['month'],day=1))
        df = df.set_index('date')
        df['days_in_month'] = df.index.days_in_month
        # Convert into discharge units
        df_selected = df.drop(['year','month','days_in_month'],axis=1)
        discharge = pd.DataFrame(df_selected.values*1000*basin_level3.values,columns=df_selected.columns)
        discharge['days_in_month'] = df['days_in_month'].values
        discharge = discharge.loc[:, discharge.columns != 'days_in_month'].divide(discharge["days_in_month"]*24*3600, axis="index")
        discharge['date'] = df.index.values
        discharge = discharge.set_index('date')
        discharge['year'] = df['year'].values
        discharge['month'] = df['month'].values
        # Aggregate discharge
        aggregate_discharge = pd.DataFrame()
        aggregate_discharge['year'] = discharge['year']
        aggregate_discharge['month'] = discharge['month']
        discharge = discharge.drop(['year','month'],axis=1)
        aggregate_discharge['discharge'] = discharge.sum(axis=1)
        # extract only the forecast
        forecast_rows = aggregate_discharge.iloc[-7:]
        df_list.append(forecast_rows)
        aggregate_discharge = aggregate_discharge.iloc[:-6,:]

    concat_df = pd.concat(df_list)
    return aggregate_discharge, concat_df

# %% [markdown]
# ## Generar Quintiles

# %%
ENSEMBLE_PERCENTAGE = pd.DataFrame()
ENSEMBLE_PERCENTAGE['codigo'] = allbasins_n2.columns
ENSEMBLE_PERCENTAGE['LowFlow'] = np.nan
ENSEMBLE_PERCENTAGE['BelowNormal'] = np.nan
ENSEMBLE_PERCENTAGE['NormalRange'] = np.nan
ENSEMBLE_PERCENTAGE['AboveNormal'] = np.nan
ENSEMBLE_PERCENTAGE['HighFlow'] = np.nan

forecast_leadtime = int(args.forecast_leadtime)


for basin in allbasins_n2.columns:
    aggregate_discharge, concat_df = importmodelensemble(basin)
    DISCHARGE_SELECTION = aggregate_discharge[(aggregate_discharge['year'] >= 1991) & (aggregate_discharge['year'] <= 2020)]
    percentiles = DISCHARGE_SELECTION.groupby(DISCHARGE_SELECTION.month).quantile([0.10,0.25,0.75,0.90])
    percentiles = percentiles.reset_index()
    percentiles = percentiles.drop(columns=['year'])
    percentiles.rename(columns={'level_1':'percentile','discharge':'discharge_percentile'}, inplace=True)

    max_values = DISCHARGE_SELECTION.groupby(DISCHARGE_SELECTION.month).max()
    max_values = max_values.drop(columns=['year'])
    min_values = DISCHARGE_SELECTION.groupby(DISCHARGE_SELECTION.month).min()
    min_values = min_values.drop(columns=['year'])

    concat_df['percentile_range'] = ''
    concat_df['percentile_range_summary'] = ''
    values_months = ['Low Flow','Below Normal','Normal Range','Above Normal','High Flow']
    values_months_summary = ['Low','Normal','High']
    discharge_plot = aggregate_discharge.loc[start_date_str:end_date_str]
    discharge_plot = discharge_plot.reset_index()

    # create empty columns in the dataframe
    discharge_plot['10th_percentile'] = np.nan
    discharge_plot['25th_percentile'] = np.nan
    discharge_plot['75th_percentile'] = np.nan
    discharge_plot['90th_percentile'] = np.nan

    for i in range(len(discharge_plot)):
        # Extract the current month 
        m = discharge_plot.month[i]
        discharge_plot.loc[discharge_plot.eval('month==@m'),'minimum']  = percentiles.query('month==@m & percentile==0.10')['discharge_percentile'].item()
        discharge_plot.loc[discharge_plot.eval('month==@m'),'10th_percentile']  = percentiles.query('month==@m & percentile==0.10')['discharge_percentile'].item()
        discharge_plot.loc[discharge_plot.eval('month==@m'),'25th_percentile']  = percentiles.query('month==@m & percentile==0.25')['discharge_percentile'].item()
        discharge_plot.loc[discharge_plot.eval('month==@m'),'75th_percentile']  = percentiles.query('month==@m & percentile==0.75')['discharge_percentile'].item()
        discharge_plot.loc[discharge_plot.eval('month==@m'),'90th_percentile']  = percentiles.query('month==@m & percentile==0.90')['discharge_percentile'].item()

    concat_df = concat_df.reset_index()
    concat_df['group'] = concat_df.index // 7

    for i in range(len(concat_df)):
        # Extract the current month 
        m = concat_df.month[i]
        y = concat_df.year[i]
        # pmin = min_values.query('month==@m')['discharge'].item()
        pmin = 0
        p90 = percentiles.query('percentile == 0.90 & month==@m')['discharge_percentile'].item()
        p75 = percentiles.query('percentile == 0.75 & month==@m')['discharge_percentile'].item()
        p25 = percentiles.query('percentile == 0.25 & month==@m')['discharge_percentile'].item()
        p10 = percentiles.query('percentile == 0.10 & month==@m')['discharge_percentile'].item()
        pmax = max_values.query('month==@m')['discharge'].item()
        value = concat_df.discharge[i]
        category = pd.cut([value],bins=[pmin,p10,p25,p75,p90,pmax],labels=values_months)
        category_summary = pd.cut([value],bins=[pmin,p25,p75,pmax],labels=values_months_summary)
        concat_df.loc[concat_df.eval('index==@i'),'percentile_range'] = category[0]
        concat_df.loc[concat_df.eval('index==@i'),'percentile_range_summary'] = category_summary[0]

    month_outlook = discharge_plot['month'].iloc[-1] + forecast_leadtime

    if month_outlook > 12:
        month_outlook = month_outlook - 12

    category_counts = concat_df.query('month==@month_outlook')['percentile_range'].value_counts()
    category_counts = category_counts.to_frame()
    category_counts = category_counts.sort_index(key=lambda x: x.map({val:idx for idx,val in enumerate(values_months)}))

    category_counts_summary = concat_df.query('month==@month_outlook')['percentile_range_summary'].value_counts()
    category_counts_summary = category_counts_summary.to_frame()
    category_counts_summary = category_counts_summary.sort_index(key=lambda x: x.map({val:idx for idx,val in enumerate(values_months_summary)}))

    category_counts['percentage_ensemble'] = round((category_counts['percentile_range']/category_counts['percentile_range'].sum())*100,1)
    category_counts_summary['percentage_ensemble'] = round((category_counts_summary['percentile_range_summary']/category_counts_summary['percentile_range_summary'].sum())*100,1)

    query_result = category_counts.query('index == "Low Flow"')['percentage_ensemble']
    if not query_result.empty:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'LowFlow'] = category_counts.query('index == "Low Flow"')['percentage_ensemble'].item()
    else:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'LowFlow'] = 0

    query_result = category_counts.query('index == "Below Normal"')['percentage_ensemble']
    if not query_result.empty:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'BelowNormal'] = category_counts.query('index == "Below Normal"')['percentage_ensemble'].item()
    else:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'BelowNormal'] = 0

    query_result = category_counts.query('index == "Normal Range"')['percentage_ensemble']
    if not query_result.empty:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'NormalRange'] = category_counts.query('index == "Normal Range"')['percentage_ensemble'].item()
    else:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'NormalRange'] = 0

    query_result = category_counts.query('index == "Above Normal"')['percentage_ensemble']
    if not query_result.empty:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'AboveNormal'] = category_counts.query('index == "Above Normal"')['percentage_ensemble'].item()
    else:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'AboveNormal'] = 0

    query_result = category_counts.query('index == "High Flow"')['percentage_ensemble']
    if not query_result.empty:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'HighFlow'] = category_counts.query('index == "High Flow"')['percentage_ensemble'].item()
    else:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'),'HighFlow'] = 0

# %%
month_outlook

# %%
ENSEMBLE_PERCENTAGE.to_csv(f'd:/Documentos/Python Scripts/Balance Hidrico/forplotting/{forecast_leadtime}_month_outlook.csv',index=False)
print('Archivo exportado correctamente')

