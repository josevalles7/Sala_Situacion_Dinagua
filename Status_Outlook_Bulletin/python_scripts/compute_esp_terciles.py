import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
import argparse
import sys
import matplotlib.pyplot as plt
from scipy.stats import mstats

'''
print(f"Old Directory: {os.getcwd()}")
os.chdir(r'../')
print(f"New Directory: {os.getcwd()}")
'''
# Define the path to the python HydroSOS Package
sys.path.append(os.path.abspath('.'))
import HydroSOS_scripts.flow_aggregation as flowagg


# Define arguments

parser = argparse.ArgumentParser(
                    prog='ESP_outlook_tertiles',
                    description='Postprocess the ESP outlook products',
                    epilog='Jose Valles, DINAGUA, 08Nov2024')

parser.add_argument('end_date', help='end date for the discharge plot in format YYYY-MM-DD')
parser.add_argument('codcuenca_n2', help='enter the codigo_n2 of the basin to plot (e.g. 60)')
parser.add_argument('leadtime', help='provide forecast leadtime')

args = parser.parse_args()
'''
args = argparse.Namespace(
    end_date='2026-04-30',
    codcuenca_n2='60',
    leadtime='3'
)
'''
end_date = args.end_date
codigo = args.codcuenca_n2
leadtime = args.leadtime

# ------------------------------------------------------------------------------
# Hydrological Status Parameters
# ------------------------------------------------------------------------------
stdStart = 1981
stdEnd = 2010

# ------------------------------------------------------------------------------
# Importing Files
# ------------------------------------------------------------------------------
allbasins_n2 = pd.read_csv('./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel2.csv', 
                           index_col="Codigo")

# Pre-load constant files once
_basin_level3_full = pd.read_csv('./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel3.csv')
_esp_folder = './waterbalance/balance_hidrico_regional/output_modelo/esp/'
_esp_file_list = [f for f in os.listdir(_esp_folder) if f.endswith('.csv')]

# Precompute basin->level3 column mapping once (avoids repeated prefix scans)
_basin_level3_map = {
    str(basin): [c for c in _basin_level3_full.columns if c.startswith(str(basin))]
    for basin in allbasins_n2.columns
}

# Cache ESP files in memory to avoid repeated disk I/O per basin
_esp_raw_cache = {}

def _get_esp_raw(file_path):
    if file_path not in _esp_raw_cache:
        _esp_raw_cache[file_path] = pd.read_csv(file_path)
    return _esp_raw_cache[file_path]

# Define the probabilities for quantile calculation
probs = [0.10, 0.25, 0.75, 0.90]


# Calculate start date as one year before the provided end date
if isinstance(end_date, str):
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

start_date = end_date - timedelta(days=365)

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')



def importmodelensemble(codcuenca_n2):
    prefix = str(codcuenca_n2)
    basin_level3_cols = _basin_level3_map.get(prefix, [])
    basin_level3 = _basin_level3_full[basin_level3_cols].values

    df_list = []

    for file in _esp_file_list:
        file_path = os.path.join(_esp_folder, file)

        # Read once per file (cached), then slice only needed columns for this basin
        raw_df = _get_esp_raw(file_path)
        selected_cols = [c for c in raw_df.columns if c.startswith(prefix) or c in ('-1', '-1.1')]
        df = raw_df[selected_cols].copy()
        df = df.rename(columns={'-1': 'year', '-1.1': 'month'})

        # Build monthly date index and unit conversion using NumPy arrays to reduce DataFrame overhead
        date_index = pd.to_datetime(dict(year=df['year'], month=df['month'], day=1))
        days_in_month = date_index.dt.days_in_month.to_numpy(dtype=float)

        # Compute basin aggregate directly (without creating intermediate per-subbasin DataFrames)
        flow_values = df.drop(['year', 'month'], axis=1).to_numpy(dtype=float)
        aggregate_flow = (flow_values * basin_level3).sum(axis=1) * 1000.0 / (days_in_month * 86400.0)

        aggregate_discharge = pd.DataFrame({
            'date': date_index,
            'year': df['year'].to_numpy(),
            'month': df['month'].to_numpy(),
            'discharge': aggregate_flow
        }).set_index('date')

        # Extract only forecast window for ensemble classification
        df_list.append(aggregate_discharge.iloc[-7:].copy())
        aggregate_discharge = aggregate_discharge.iloc[:-6, :]

    concat_df = pd.concat(df_list)
    return aggregate_discharge, concat_df

def classify_terciles(values, p25, p75, labels):
    """Classify values into terciles using only p25 and p75 thresholds.
    This guarantees that values > p75 are classified as Above Normal
    (no upper cap that could leave values unclassified).
    """
    values = np.asarray(values, dtype=float)
    out = np.full(values.shape, np.nan, dtype=object)

    if np.isfinite(p25) and np.isfinite(p75) and (p25 < p75):
        out[values < p25] = labels[0]
        out[(values >= p25) & (values <= p75)] = labels[1]
        out[values > p75] = labels[2]

    return pd.Categorical(out, categories=labels, ordered=True)


def fill_row_percentages(row, counts, total, category_map):
    """Fill row percentages and force exact closure to 100.0 after rounding."""
    items = list(category_map.items())

    if total <= 0:
        for _, col in items:
            row[col] = 0.0
        return

    v1 = round(counts.get(items[0][0], 0) / total * 100, 1)
    v2 = round(counts.get(items[1][0], 0) / total * 100, 1)
    # v3 = round(100.0 - v1 - v2, 1)
    v3 = round(counts.get(items[2][0], 0) / total * 100, 1)

    row[items[0][1]] = v1
    row[items[1][1]] = v2
    row[items[2][1]] = v3

def group_quantiles_mstats(series, probs, alphap, betap):
    """Apply mstats.mquantiles to a GroupBy group, returning a Series."""
    q = mstats.mquantiles(series.dropna().values, probs, alphap=alphap, betap=betap)
    return pd.Series(q, index=probs)


values_months = ['Below Normal', 'Normal Range', 'Above Normal']
values_months_summary = ['Low', 'Normal', 'High']
category_col_map = {'Below Normal': 'BelowNormal', 'Normal Range': 'NormalRange', 'Above Normal': 'AboveNormal'}

basin_discharge = {}
basin_ensemble = {}
results_1month = []
results_2month = []
results_3month = []
basin_climate_1month = {}
basin_climate_2month = {}
basin_climate_3month = {}

for basin in allbasins_n2.columns:
    discharge, concat_df = importmodelensemble(basin)

    # Rename for compatibility with hydrostatus and compute rolling-mean products once
    discharge = discharge.rename(columns={'discharge': 'mean_flow'})
    discharge_twomonths = flowagg.calculate_accumulated(discharge, 2)
    discharge_threemonths = flowagg.calculate_accumulated(discharge, 3)

    # Historical climatology by scale
    discharge_std = discharge[(discharge['year'] >= stdStart) & (discharge['year'] <= stdEnd)]
    # calculate percentile using Weibull formula. For Cunnane use alphap=0.4, betap=0.4 
    pct_dict_1m = (
                discharge_std
                .groupby('month')['mean_flow']
                .apply(group_quantiles_mstats, probs=probs, alphap=0, betap=0)
            ).to_dict()

    discharge_twomonths_std = discharge_twomonths[(discharge_twomonths['year'] >= stdStart) & (discharge_twomonths['year'] <= stdEnd)]
    # calculate percentile using Weibull formula. For Cunnane use alphap=0.4, betap=0.4 
    pct_dict_2m = (
                discharge_twomonths_std
                .groupby('month')['mean_flow']
                .apply(group_quantiles_mstats, probs=probs, alphap=0, betap=0)
            ).to_dict()

    discharge_threemonths_std = discharge_threemonths[(discharge_threemonths['year'] >= stdStart) & (discharge_threemonths['year'] <= stdEnd)]
    # calculate percentile using Weibull formula. For Cunnane use alphap=0.4, betap=0.4 
    pct_dict_3m = (
                discharge_threemonths_std
                .groupby('month')['mean_flow']
                .apply(group_quantiles_mstats, probs=probs, alphap=0, betap=0)
            ).to_dict()
    # Prepare forecast ensemble table once
    concat_df = concat_df.reset_index(drop=False)
    concat_df['group'] = concat_df.index // 7

    # Determine outlook months directly from end_date (avoids extra temporary DataFrame)
    last_month = end_date.month
    month_1m = (last_month % 12) + 1
    month_2m = ((last_month + 1) % 12) + 1
    month_3m = ((last_month + 2) % 12) + 1

    row_1m = {'codigo': basin}
    row_2m = {'codigo': basin}
    row_3m = {'codigo': basin}

    # 1-month outlook
    p25_1m = pct_dict_1m.get((month_1m, 0.25), np.nan)
    p75_1m = pct_dict_1m.get((month_1m, 0.75), np.nan)
    vals_1m = concat_df.loc[concat_df['month'] == month_1m, 'discharge'].to_numpy(dtype=float)
    outlook_1m = pd.Series(classify_terciles(vals_1m, p25_1m, p75_1m, values_months))

    counts_1m = outlook_1m.value_counts()
    total_1m = int(counts_1m.sum())
    fill_row_percentages(row_1m, counts_1m, total_1m, category_col_map)

    # 1-2 month outlook
    ensemble_2m = concat_df[concat_df['month'].isin([month_1m, month_2m])].groupby('group')['discharge'].mean()
    p25_2m = pct_dict_2m.get((month_2m, 0.25), np.nan)
    p75_2m = pct_dict_2m.get((month_2m, 0.75), np.nan)
    outlook_2m = pd.Series(classify_terciles(ensemble_2m.to_numpy(dtype=float), p25_2m, p75_2m, values_months))

    counts_2m = outlook_2m.value_counts()
    total_2m = int(counts_2m.sum())
    fill_row_percentages(row_2m, counts_2m, total_2m, category_col_map)

    # 1-3 month outlook
    ensemble_3m = concat_df[concat_df['month'].isin([month_1m, month_2m, month_3m])].groupby('group')['discharge'].mean()
    p25_3m = pct_dict_3m.get((month_3m, 0.25), np.nan)
    p75_3m = pct_dict_3m.get((month_3m, 0.75), np.nan)
    outlook_3m = pd.Series(classify_terciles(ensemble_3m.to_numpy(dtype=float), p25_3m, p75_3m, values_months))

    counts_3m = outlook_3m.value_counts()
    total_3m = int(counts_3m.sum())
    fill_row_percentages(row_3m, counts_3m, total_3m, category_col_map)

    results_1month.append(row_1m)
    results_2month.append(row_2m)
    results_3month.append(row_3m)

    basin_discharge[basin] = discharge
    basin_ensemble[basin] = concat_df
    basin_climate_1month[basin] = discharge_std
    basin_climate_2month[basin] = discharge_twomonths_std
    basin_climate_3month[basin] = discharge_threemonths_std


# Build DataFrames for each horizon
results_1month_df = pd.DataFrame(results_1month)
results_2month_df = pd.DataFrame(results_2month)
results_3month_df = pd.DataFrame(results_3month)


# Stacked tercile plot for basin codigo 60 across forecast horizons
row_1m = results_1month_df[results_1month_df['codigo'].astype(str) == codigo].iloc[0]
row_2m = results_2month_df[results_2month_df['codigo'].astype(str) == codigo].iloc[0]
row_3m = results_3month_df[results_3month_df['codigo'].astype(str) == codigo].iloc[0]

# Dynamic month labels from end_date
month_1m = (end_date.month % 12) + 1
month_2m = ((end_date.month + 1) % 12) + 1
month_3m = ((end_date.month + 2) % 12) + 1
month_names = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}

def add_months(year, month, delta):
    """Return (year, month) after adding delta months to the given year-month."""
    total = year * 12 + (month - 1) + delta
    return total // 12, (total % 12) + 1


def build_horizon_label(end_date, horizon, month_names):
    """Format labels like:
    1M  -> Dic 2025
    2M  -> Dic - Ene 2025/26 (if crossing years)
    3M  -> Dic - Feb 2025/26 (first-to-last only)
    """
    months_years = [add_months(end_date.year, end_date.month, d) for d in range(1, horizon + 1)]

    first_month = month_names[months_years[0][1]]
    last_month = month_names[months_years[-1][1]]

    if horizon == 1:
        month_text = first_month
    else:
        # Keep labels compact: for 2M and 3M use first-to-last month only
        month_text = f'{first_month} - {last_month}'

    y0 = months_years[0][0]
    y1 = months_years[-1][0]
    if y0 == y1:
        year_text = f'{y0}'
    else:
        year_text = f'{y0}/{str(y1)[-2:]}'

    return f'{month_text} {year_text}'


month_labels = [
    build_horizon_label(end_date, 1, month_names),
    build_horizon_label(end_date, 2, month_names),
    build_horizon_label(end_date, 3, month_names),
]

below = [row_1m['BelowNormal'], row_2m['BelowNormal'], row_3m['BelowNormal']]
normal = [row_1m['NormalRange'], row_2m['NormalRange'], row_3m['NormalRange']]
above = [row_1m['AboveNormal'], row_2m['AboveNormal'], row_3m['AboveNormal']]

plt.figure(figsize=(9, 5))
plt.bar(month_labels, below, label='Inferior', color='#CD233F')
plt.bar(month_labels, normal, bottom=below, label='Rango Normal', color='#E7E2BC')
plt.bar(month_labels, above, bottom=[b + n for b, n in zip(below, normal)], label='Superior', color='#2C7DCD')

# plt.xlabel('Horizonte de Pronóstico')
plt.title(f'Perspectiva hidrológica - Codigo {codigo}')

# Hide y-axis visuals (label, ticks and left vertical spine)
ax = plt.gca()
ax.yaxis.set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

# plot legend outside the plot area and horizontally
plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
# inside the bar include the percentage value with white color and bold font
for i, (b, n, a) in enumerate(zip(below, normal, above)):
    total = b + n + a
    if b > 0:
        plt.text(i, b / 2, f'{b}%', ha='center', va='center', color='white', fontweight='bold')
    if n > 0:
        plt.text(i, b + n / 2, f'{n}%', ha='center', va='center', color='black', fontweight='bold')
    if a > 0:
        plt.text(i, b + n + a / 2, f'{a}%', ha='center', va='center', color='white', fontweight='bold') 

plt.tight_layout()
plt.savefig(f"./waterbalance/output_png/09_barstacked_outlook.png", dpi=300, bbox_inches='tight')
plt.close()

## Plotting probability of excedeence
# Outlook months derived from end_date
month_1 = (end_date.month % 12) + 1
month_2 = ((end_date.month + 1) % 12) + 1
month_3 = ((end_date.month + 2) % 12) + 1

# Reuse the same dynamic labeling logic as the stacked tercile plot
label_1m = build_horizon_label(end_date, 1, month_names)
label_2m = build_horizon_label(end_date, 2, month_names)
label_3m = build_horizon_label(end_date, 3, month_names)

# Ensemble forecast for this basin
esp = basin_ensemble[codigo].reset_index(drop=False)
esp['group'] = esp.index // 7

# Aggregate ensemble values per member for each horizon
forecast_1m = esp.loc[esp['month'] == month_1, 'discharge'].dropna().sort_values().values
forecast_2m = esp[esp['month'].isin([month_1, month_2])].groupby('group')['discharge'].mean().sort_values().values
forecast_3m = esp[esp['month'].isin([month_1, month_2, month_3])].groupby('group')['discharge'].mean().sort_values().values

scales = [
    (basin_climate_1month, [month_1],                   label_1m, forecast_1m),
    (basin_climate_2month, [month_1, month_2],          label_2m, forecast_2m),
    (basin_climate_3month, [month_1, month_2, month_3], label_3m, forecast_3m),
]

fig, axes = plt.subplots(1, 3, figsize=(10, 4))

for i, (ax, (climate_dict, months, label, forecast_vals)) in enumerate(zip(axes, scales)):
    # Climatology curve
    data = climate_dict[codigo]
    flow_values = data[data['month'].isin(months)]['mean_flow'].dropna().sort_values().values
    n = len(flow_values)
    exceedance = 1 - (np.arange(1, n + 1) / (n + 1))
    line_clim, = ax.plot(flow_values, exceedance * 100, color='steelblue', linewidth=2, label='Referencia Histórica')

    # Forecast ensemble curve
    nf = len(forecast_vals)
    exc_forecast = 1 - (np.arange(1, nf + 1) / (nf + 1))
    line_esp, = ax.plot(forecast_vals, exc_forecast * 100, color='red', linewidth=2, linestyle='--', label='Pronóstico')

    # Month label as subplot subtitle
    ax.set_title(label, fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=12)

    # Y-axis label only on the leftmost subplot
    if i == 0:
        ax.set_ylabel('Probabilidad de excedencia (%)', fontsize=12)
    else:
        ax.set_ylabel('')
        ax.tick_params(labelleft=False)

    # Box (all four spines visible)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)

    # Minor ticks on y-axis
    ax.yaxis.set_minor_locator(plt.MultipleLocator(5))
    ax.tick_params(axis='y', which='minor', length=3)

    # Dashed grey grid with custom dash pattern (major only)
    ax.grid(True, which='major', color='grey', linewidth=0.5, alpha=0.6)
    for gl in ax.yaxis.get_gridlines() + ax.xaxis.get_gridlines():
        gl.set_linestyle('--')
        gl.set_dashes((5, 10))
    ax.set_axisbelow(True)

    ax.set_ylim(0, 100)
    ax.set_xlim(left=0)

    # Legend inside the third subplot only
    if i == 2:
        ax.legend(handles=[line_clim, line_esp], loc='upper right', fontsize=12, frameon=True)

# Single shared x-axis label centered below all subplots
fig.text(0.5, -0.02, 'Caudal medio (m³/s)', ha='center', va='center', fontsize=12)

plt.tight_layout()
plt.savefig(f"./waterbalance/output_png/10_FDC_outlook.png", dpi=300, bbox_inches='tight')
plt.close()