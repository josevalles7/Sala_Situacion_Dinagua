
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use('classic')
import numpy as np
from datetime import datetime, timedelta
import argparse
import sys
from scipy.stats import mstats


'''
print(f"Old Directory: {os.getcwd()}")
os.chdir(r'../')
print(f"New Directory: {os.getcwd()}")
'''

sys.path.append(os.path.abspath('.'))
import HydroSOS_scripts.flow_aggregation as flowagg
import HydroSOS_scripts.hydrological_status as SOS



# Define arguments 
parser = argparse.ArgumentParser(
                    prog='ESP_outlook_tertiles',
                    description='Postprocess the ESP outlook products',
                    epilog='Jose Valles, DINAGUA, 08Nov2024')

# 
parser.add_argument('forecast_leadtime', help='provide forecast leadtime')
parser.add_argument('end_date', help='end date for the discharge plot in format YYYY-MM-DD')

args = parser.parse_args()
'''
args = argparse.Namespace(
    forecast_leadtime='3',
    end_date='2026-04-30',
)
'''

# ------------------------------------------------------------------------------
# Date Management
# ------------------------------------------------------------------------------
end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
start_date = end_date - timedelta(days=365)  # Subtracting 365 days for a year difference
# Format dates as strings
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')
# Importing basin file
allbasins_n2 = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel2.csv',index_col="Codigo")


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
stdStart = 1981
stdEnd = 2010
# Define the Three outlook categories (3) and their corresponding column names
values_months = ['Below Normal', 'Normal Range', 'Above Normal']
category_col_map = {'Below Normal': 'BelowNormal', 'Normal Range': 'NormalRange', 'Above Normal': 'AboveNormal'}
# Define the Five outlook categories (5) and their corresponding column names
values_months_5 = ['Low Flow', 'Below Normal', 'Normal Range', 'Above Normal', 'High Flow']
category_col_map_5 = {'Low Flow': 'LowFlow', 'Below Normal': 'BelowNormal', 'Normal Range': 'NormalRange', 'Above Normal': 'AboveNormal', 'High Flow': 'HighFlow'}
# Define the probabilities for quantile calculation
probs = [0.10, 0.25, 0.75, 0.90]


def importmodelensemble(codcuenca_n2):
    basin_level3 = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel3.csv',usecols=lambda col: col.startswith(str(codcuenca_n2)))
    basin_level2 = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel2.csv',usecols=lambda col: col.startswith(str(codcuenca_n2)))
    # Insert the folder path 
    folder_path = './waterbalance/balance_hidrico_regional/output_modelo/esp/'
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

def group_quantiles_mstats(series, probs, alphap, betap):
    """Apply mstats.mquantiles to a GroupBy group, returning a Series."""
    q = mstats.mquantiles(series.dropna().values, probs, alphap=alphap, betap=betap)
    return pd.Series(q, index=probs)


def classify_terciles(values, p25, p75, labels):
    """Classify values into terciles using p25 and p75 thresholds."""
    values = np.asarray(values, dtype=float)
    out = np.full(values.shape, np.nan, dtype=object)
    if np.isfinite(p25) and np.isfinite(p75) and (p25 < p75):
        out[values < p25] = labels[0]
        out[(values >= p25) & (values <= p75)] = labels[1]
        out[values > p75] = labels[2]
    return pd.Categorical(out, categories=labels, ordered=True)

def classify_quintiles(values, p10, p25, p75, p90, labels):
    """Classify values into quintiles using p10, p25, p75, and p90 thresholds."""
    values = np.asarray(values, dtype=float)
    out = np.full(values.shape, np.nan, dtype=object)
    if np.isfinite(p10) and np.isfinite(p25) and np.isfinite(p75) and np.isfinite(p90) and (p10 < p25 < p75 < p90):
        out[values < p10] = labels[0]
        out[(values >= p10) & (values < p25)] = labels[1]
        out[(values >= p25) & (values <= p75)] = labels[2]
        out[(values > p75) & (values <= p90)] = labels[3]
        out[values > p90] = labels[4]
    return pd.Categorical(out, categories=labels, ordered=True)


def fill_row_percentages(row, counts, total, category_map):
    """Fill row percentages for each category."""
    items = list(category_map.items())
    if total <= 0:
        for _, col in items:
            row[col] = 0.0
        return
    row[items[0][1]] = round(counts.get(items[0][0], 0) / total * 100, 1)
    row[items[1][1]] = round(counts.get(items[1][0], 0) / total * 100, 1)
    row[items[2][1]] = round(counts.get(items[2][0], 0) / total * 100, 1)


# Create output dataframe with basin code and percentage columns for each category
ENSEMBLE_PERCENTAGE = pd.DataFrame()
ENSEMBLE_PERCENTAGE['codigo'] = allbasins_n2.columns
ENSEMBLE_PERCENTAGE['BelowNormal'] = np.nan
ENSEMBLE_PERCENTAGE['NormalRange'] = np.nan
ENSEMBLE_PERCENTAGE['AboveNormal'] = np.nan

# assign the forecast leadtime to a variable for easier use. If the leadtime is not 1, 2, or 3, print an error message and exit the program
forecast_leadtime = int(args.forecast_leadtime)
if forecast_leadtime not in [1, 2, 3]:
    print(f"Unsupported forecast leadtime: {forecast_leadtime}. Supported values are 1, 2, or 3.")
    sys.exit(1)


# Determine outlook months from end_date
# month_1 is 1 month ahead, month_2 is 2 months ahead, month_3 is 3 months ahead
month_1 = (end_date.month % 12) + 1
month_2 = ((end_date.month + 1) % 12) + 1
month_3 = ((end_date.month + 2) % 12) + 1

# Print the outlook months for verification in %B Format (e.g., January, February, etc.)    
print(
    f"Outlook months: "
    f"{pd.Timestamp(end_date.year, month_1, 1).strftime('%b-%Y')}, "
    f"{pd.Timestamp(end_date.year, month_2, 1).strftime('%b-%Y')}, "
    f"{pd.Timestamp(end_date.year, month_3, 1).strftime('%b-%Y')}"
)


# from allbasins_n2, extract the column names '60' and drop the rest
# allbasins_n2 = allbasins_n2[['60']]

# ============================================================
# Quantile calculation
# ============================================================
# Formula (scipy.stats.mstats.mquantiles):
#   p(k) = (k - alphap) / (n + 1 - alphap - betap)
#
#   k  = rank of the sorted observation (1 = smallest, n = largest)
#   n  = number of observations in the sample (e.g. 30 years of climatology)
#
#   Weibull : alphap=0,   betap=0   -> p = k / (n + 1)
#   Cunnane : alphap=0.4, betap=0.4 -> p = (k - 0.4) / (n + 0.2)
#   Pandas  : linear interpolation (Type 7) -> p = (k - 1) / (n - 1)
# ============================================================
for basin in allbasins_n2.columns:
    print(f"Processing basin {basin}...")
    # Import the discharge data for the current basin
    aggregate_discharge, concat_df = importmodelensemble(basin)
    # the outlook forecast (concat_df) is expected to have 7 rows corresponding to the 7 ensemble members for the forecast months, including the current month.
    # We will need to classify these 7 values into terciles or quintiles based on the climatological percentiles computed from the aggregate_discharge data. 
    # To do this, we will first need to reset the index of concat_df and create a 'group' column that identifies which rows belong to the same month (since we have 7 rows per month, we can use integer division by 7 to create this grouping).
    concat_df = concat_df.reset_index()
    concat_df['group'] = concat_df.index // 7
    # Rename for compatibility with flowagg rolling-mean functions
    discharge = aggregate_discharge.rename(columns={'discharge': 'mean_flow'})
    match forecast_leadtime:
        case 1:
            print("Calculating 1-month forecast percentages...")
            discharge_std = discharge[(discharge['year'] >= stdStart) & (discharge['year'] <= stdEnd)]
            # calculate percentile using Weibull formula. For Cunnane use alphap=0.4, betap=0.4 
            pct_dict_1m = (
                discharge_std
                .groupby('month')['mean_flow']
                .apply(group_quantiles_mstats, probs=probs, alphap=0.4, betap=0.4)
            ).to_dict()
            print("Processing 1-month lead time outlook...")
            p10 = pct_dict_1m.get((month_1, 0.10), np.nan)
            p25 = pct_dict_1m.get((month_1, 0.25), np.nan)
            p75 = pct_dict_1m.get((month_1, 0.75), np.nan)
            p90 = pct_dict_1m.get((month_1, 0.90), np.nan)
            # extract the relevant months for the 1-month outlook
            vals = concat_df.loc[concat_df['month'] == month_1, 'discharge'].to_numpy(dtype=float)
            print("...end of the 1-month lead time outlook processing.")
            # Rolling-mean climatology for 2-month and 3-month scales (computed only when needed)
        case 2:
            print("Calculating 2-month accumulated discharge and climatology...")
            discharge_twomonths = flowagg.calculate_accumulated(discharge, 2)
            discharge_twomonths_std = discharge_twomonths[
                (discharge_twomonths['year'] >= stdStart) & (discharge_twomonths['year'] <= stdEnd)
            ]
            # calculate percentile using Weibull formula. For Cunnane use alphap=0.4, betap=0.4 
            pct_dict_2m = (
                discharge_twomonths_std
                .groupby('month')['mean_flow']
                .apply(group_quantiles_mstats, probs=probs, alphap=0.4, betap=0.4)
            ).to_dict()
            print("Processing 2-month lead time outlook...")
            # extract the relevant months for the 2-month outlook and compute the mean discharge for those months
            vals = (
                concat_df[concat_df['month'].isin([month_1, month_2])]
                .groupby('group')['discharge'].mean()
                .to_numpy(dtype=float)
            )
            p10 = pct_dict_2m.get((month_2, 0.10), np.nan)
            p25 = pct_dict_2m.get((month_2, 0.25), np.nan)
            p75 = pct_dict_2m.get((month_2, 0.75), np.nan)
            p90 = pct_dict_2m.get((month_2, 0.90), np.nan)
            print("...end of the 2-month lead time outlook processing.")
        case 3:
            print("Calculating 3-month accumulated discharge and climatology...")
            discharge_threemonths = flowagg.calculate_accumulated(discharge, 3)
            discharge_threemonths_std = discharge_threemonths[
                (discharge_threemonths['year'] >= stdStart) & (discharge_threemonths['year'] <= stdEnd)
            ]
            # calculate percentile using Weibull formula. For Cunnane use alphap=0.4, betap=0.4 
            pct_dict_3m = (
                discharge_threemonths_std
                .groupby('month')['mean_flow']
                .apply(group_quantiles_mstats, probs=probs, alphap=0.4, betap=0.4)
            ).to_dict()
            print("Processing 3-month lead time outlook...")
            # extract the relevant months for the 3-month outlook and compute the mean discharge for those months
            vals = (
                concat_df[concat_df['month'].isin([month_1, month_2, month_3])]
                .groupby('group')['discharge'].mean()
                .to_numpy(dtype=float)
            )
            p10 = pct_dict_3m.get((month_3, 0.10), np.nan)
            p25 = pct_dict_3m.get((month_3, 0.25), np.nan)
            p75 = pct_dict_3m.get((month_3, 0.75), np.nan)
            p90 = pct_dict_3m.get((month_3, 0.90), np.nan)
            print("...end of the 3-month lead time outlook processing.")
        case _:
            print(f"Unsupported forecast leadtime: {forecast_leadtime}. Supported values are 1, 2, or 3.")
            sys.exit(1)

    # Three Categories (Terciles)
    outlook = pd.Series(classify_terciles(vals, p25, p75, values_months))
    # Five Categories (Quintiles)
    # outlook = pd.Series(classify_quintiles(vals, p10, p25, p75, p90, values_months_5))
    counts = outlook.value_counts()
    total = int(counts.sum())
    row = {'codigo': basin}
    fill_row_percentages(row, counts, total, category_col_map)

    for col_name in ['BelowNormal', 'NormalRange', 'AboveNormal']:
        ENSEMBLE_PERCENTAGE.loc[ENSEMBLE_PERCENTAGE.eval('codigo==@basin'), col_name] = row[col_name]


ENSEMBLE_PERCENTAGE.to_csv(f'./qgis_status_outlook/csvtables/terciles_{forecast_leadtime}_month_outlook.csv',index=False)
print('Archivo exportado correctamente')


