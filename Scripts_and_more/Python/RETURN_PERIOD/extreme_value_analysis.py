# %%
# import hydromt and functions needed for EVA
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pandas as pd
import argparse

from hydromt.stats import extremes

# %%
# Define arguments 
parser = argparse.ArgumentParser(
                    prog='extre_value_analysis',
                    description='Calculate return period from a discharge csv file',
                    epilog='Jose Valles, DINAGUA, 26032025')

# Define arguments
parser.add_argument('station', help='Provide the csv station filename')
# Parse arguments
args = parser.parse_args()

# %%
station = args.station
# We create some random continuous time series with some extremes
flowdata = pd.read_csv(f"../../Status_Outlook_Bulletin/stations/data/{station}.csv",parse_dates=['Fecha'],index_col="Fecha",dayfirst=True,na_values="NA")
# Convertir el índice a datetime por si acaso
flowdata.index = pd.to_datetime(flowdata.index, dayfirst=True)
diff = pd.date_range(start = flowdata.index[0].strftime('%Y-%m-%d'), end = flowdata.index[-1].strftime('%Y-%m-%d'),freq='D')
# Re-index the dataframe based on the missind date variable
flowdata = flowdata.reindex(diff,fill_value=None)
# Set index Fecha
flowdata.index.name = 'Fecha'
flowdata = flowdata.rename_axis("date")
# Change columns names
flowdata.columns = ['flow']

#month and year column
flowdata['month'] = flowdata.index.month
flowdata['year'] = flowdata.index.year
flowdata = flowdata.reset_index()

#check whether or not there is enough data? 
print(f"There are {flowdata['year'].max() - flowdata['year'].min()} years of data in this file.")
print(f"There are {sum(flowdata['flow'].isnull())} missing data points, which is {np.round(sum(flowdata['flow'].isnull())/len(flowdata) * 100,2)}% of the total data")

# %%
# Create DataArray with time and station dimensions
da = xr.DataArray(flowdata["flow"].values[:, np.newaxis],
                  coords={"time": flowdata["date"].values,
                          "stations": [station]},
                  dims=["time", "stations"],
                  name="discharge")

# Add attributes
da.attrs["long_name"] = "discharge"
da.attrs["units"] = "m3/s"

# %% [markdown]
# ## Step 1: Extracting peaks from continuous time series

# We use the get_peaks function
bm_peaks = extremes.get_peaks(da, ev_type="BM", period="year")

# %% [markdown]
# ## Step 2: fit a EV distribution on these peaks 

da_params = extremes.fit_extremes(bm_peaks, ev_type="BM", distribution="gev")
da_params.load()

# %% [markdown]
# ## Step 3: obtain return values for given return periods based on the distribution fitted and its parameters

# We define the return periods for which we would like to know the return values
rps = np.array([2, 5, 10, 25, 50, 100, 500])
da_rps = extremes.get_return_value(da_params, rps=rps).load()
da_rps.to_pandas()
# Create dataframe for table plotting
df_table = da_rps.to_dataframe(name="Discharge (m³/s)")
df_table.index.name = "T (years)"
df_table_reset = df_table.reset_index()

# Round values
df_table_reset["T (years)"] = df_table_reset["T (years)"].astype(int)
df_table_reset["Discharge (m³/s)"] = df_table_reset["Discharge (m³/s)"].round(2)
df_table_reset = df_table_reset.drop(columns=['stations', 'extremes_rate','distribution'])

# %% [markdown]
# ## Step 4: plot the distribution and empirical data
da_params = da_params.expand_dims("stations")
da_params = da_params.assign_coords(stations=[station])  # Asegura el valor correcto

# %%
# We plot the fit obtained using the function plot_return_values!
station_name = str(float(station)/10)
fig, ax = plt.subplots(figsize=(10, 8),sharex=True)

extremes.plot_return_values(bm_peaks.sel(stations=station),
                            da_params.sel(stations=station),
                            "gev",
                            color="black",
                            nsample=1000,
                            rps=rps,
                            extremes_rate=1.0,
                            ax=ax)

table = plt.table(cellText=df_table_reset.values,
                  colLabels=df_table_reset.columns,
                  cellLoc='center',
                  loc='bottom',
                  bbox=[0.0, -0.35, 1, 0.25])

plt.subplots_adjust(bottom=0.3)

ax.set_title(f"Station {station_name}");
ax.set_ylabel("Discharge [m3/s]");
ax.set_xlabel("Return period [years]");

plt.show()  
