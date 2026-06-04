# %%
import requests
import locale
import xlwings as xw
import datetime as datetime
from urllib.parse import urlencode
import pandas as pd
import argparse


# %%

# Define arguments 
parser = argparse.ArgumentParser(
                    prog='Get data from FEWS-UY to Excel database_report.xlsx',
                    description='Import data to Excel for Sala de Situación DINAGUA',
                    epilog='Jose Valles, DINAGUA, 08Abr2026')

# 
parser.add_argument('Q_EROGADO_SG', help='Provide outflow discharge for Salto Grande dam')
parser.add_argument('Q_EROGADO_BONETE', help='Provide outflow discharge for Bonete dam')
parser.add_argument('Q_EROGADO_PALMAR', help='Provide outflow discharge for Palmar dam') 

args = parser.parse_args()
'''
args = argparse.Namespace(
    Q_EROGADO_SG='2000 y 3000',
    Q_EROGADO_BONETE='1000 y 2000',
    Q_EROGADO_PALMAR='500 y 1000'
)
'''

# %% [markdown]
# #### Prepare function

# %%
def fetch_timeseries(
    filterId,
    locationIds,
    parameterId,
    moduleInstanceIds,
    start_time,
    end_time,
    base_url="http://testterh-fssaws:8080/FewsWebServices/rest/fewspiservice/v1/timeseries",
):
    """
    Build the URL and params for a FEWS PI REST timeseries request.

    Returns
    -------
    tuple : (url, params)
    """
    query = (
        [("filterId", filterId)]
        + [("locationIds", loc) for loc in locationIds]
        + [("parameterIds", parameterId)]
        + [("moduleInstanceIds", m) for m in moduleInstanceIds]
        + [("startTime", start_time), ("endTime", end_time)]
    )
    url = f"{base_url}?{urlencode(query)}"
    params = {"documentVersion": "1.23", "documentFormat": "PI_JSON"}
    return url, params


def parse_timeseries(data):
    """
    Parse a PI_JSON timeseries response into a dict of DataFrames keyed by locationId.

    Parameters
    ----------
    data : dict   Parsed JSON response from the FEWS PI REST service

    Returns
    -------
    dict : {locationId: pd.DataFrame} with columns ["value", "flag", "parameterId"]
    """
    dfs = {}
    for ts in data.get("timeSeries", []):
        header = ts["header"]
        location = header["locationId"]
        parameter = header["parameterId"]

        df = pd.DataFrame(ts.get("events", []))
        if df.empty:
            continue
        df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])
        df = df.set_index("datetime")[["value", "flag"]]
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df[df["flag"] != "8"]
        df["parameterId"] = parameter

        if location in dfs:
            dfs[location] = pd.concat([dfs[location], df])
        else:
            dfs[location] = df

    print(f"Locations loaded: {list(dfs.keys())}")
    return dfs


def write_values_to_excel(wb, dfs, mapping, offsets=None, decimals=2, anchor_time=None):
    """
    Write the latest timeseries value and optionally offset values into an Excel workbook.

    Parameters
    ----------
    wb : xlwings.Book
    dfs : dict {locationId: pd.DataFrame}
    mapping : dict {locationId: {"basin": str, "cell": str}}
    offsets : list of pd.Timedelta, optional
        Time offsets relative to the base timestamp. Each offset is written
        to successive rows (cell+1, cell+2, ...).
    decimals : int
        Decimal places for rounding.
    anchor_time : pd.Timestamp, optional
        If provided, the base timestamp is set to the nearest available value
        to this time instead of the last value in the series. Useful for
        forecast data where the base should be a specific lead time (e.g. tomorrow).
    """
    for location, info in mapping.items():
        df = dfs.get(location)
        if df is None or df.empty or "value" not in df.columns:
            continue
        values = df["value"].dropna()
        if values.empty:
            continue

        basin, cell = info["basin"], info["cell"]
        col, base_row = cell[0], int(cell[1:])

        if anchor_time is not None:
            idx = values.index.get_indexer([anchor_time], method="nearest")[0]
            base_time = values.index[idx]
            base_value = round(values.iloc[idx], decimals)
        else:
            base_time = values.index[-1]
            base_value = round(values.iloc[-1], decimals)

        wb.sheets[basin].range(cell).value = base_value

        offset_log = []
        for i, offset in enumerate(offsets or [], start=1):
            target = base_time + offset
            match = values[values.index == target]
            offset_value = round(match.iloc[0], decimals) if not match.empty else None
            if offset_value is not None:
                wb.sheets[basin].range(f"{col}{base_row + i}").value = offset_value
            offset_log.append(f"  offset[{i}] {target:%Y-%m-%d %H:%M} -> {offset_value}")

        print(
            f"Location: {location} | Basin: {basin} | "
            f"Base: {base_time:%Y-%m-%d %H:%M} = {base_value}"
            + ("\n" + "\n".join(offset_log) if offset_log else "")
        )


# %% [markdown]
# #### Water stage (h.obs) for the flood report

# %%
filterId = "FEWS-UY"
loc_stage_sim = ["2206", "2257", "0000", "2215","2145",
               "A50C65E2","A5006AAC","A50079DA","A50C9566","A5004292","A501258E",
               "44.0","53.1","59.1","133.0","10.1","115.0",
               "2235","2232","1826"]
par_stage_sim = "H.obs"
mod_stage_sim = ["ImportUTE", "ImportCTM","ImportDINAGUA","ImportINA"]

# get UTC time now
end_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
# start_time is end_time minus 12 hours
start_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=80)).strftime("%Y-%m-%dT%H:%M:%SZ")

url_stage_sim, params_stage_sim = fetch_timeseries(
    filterId,
    loc_stage_sim,
    par_stage_sim,
    mod_stage_sim,
    start_time,
    end_time,
)

# %%
loc_precip_sim = ["56","43","60","61","10","65"]
par_precip_sim = "P.cuenca"
mod_precip_sim = ["PreprocessP"]

url_precip, params_precip = fetch_timeseries(
    filterId,
    loc_precip_sim,
    par_precip_sim,
    mod_precip_sim,
    start_time,
    end_time,
)

# %%
loc_precip_fcst = ["56","43","60","61","10","65"]
par_precip_fcst = "P.pro"
mod_precip_fcst = ["PreprocessGFS"]
end_fcst = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%SZ")

url_precip_fcst, params_precip_fcst = fetch_timeseries(
    filterId,
    loc_precip_fcst,
    par_precip_fcst,
    mod_precip_fcst,
    start_time,
    end_fcst,
)

# %%
response_stage_sim = requests.get(url_stage_sim,params=params_stage_sim)
print(response_stage_sim.status_code)

response_precip_sim = requests.get(url_precip,params=params_precip)
print(response_precip_sim.status_code)

response_precip_fcst = requests.get(url_precip_fcst,params=params_precip_fcst)
print(response_precip_fcst.status_code)

data_stage_sim = response_stage_sim.json()
data_precip_sim = response_precip_sim.json()
data_precip_fcst = response_precip_fcst.json()

# close the request
response_stage_sim.close()
response_precip_sim.close()
response_precip_fcst.close()

# %%
dfs_stage_sim = parse_timeseries(data_stage_sim)
dfs_precip_sim = parse_timeseries(data_precip_sim)
dfs_precip_fcst = parse_timeseries(data_precip_fcst)

# %%
# create a mapping of locationId to basin and excel cell location
location_basin_mapping = {
    "2206": {"basin": "YI", "cell": "C16"},
    "2257": {"basin": "YI", "cell": "C6"},
    "0000": {"basin": "YI", "cell": "C11"},
    "2215": {"basin": "YI", "cell": "C2"},
    "2145": {"basin": "NEGRO", "cell": "C7"},
    "1826": {"basin": "NEGRO", "cell": "C2"},
    "A50C65E2": {"basin": "CUAREIM", "cell": "C12"},
    "A5006AAC": {"basin": "CUAREIM", "cell": "C2"},
    "A50079DA": {"basin": "CUAREIM", "cell": "C7"},
    "A50C9566": {"basin": "URUGUAY", "cell": "C7"},
    "A5004292": {"basin": "URUGUAY", "cell": "C2"},
    "A501258E": {"basin": "URUGUAY", "cell": "C12"},
    "44.0": {"basin": "SANTALUCIA", "cell": "C2"},
    "53.1": {"basin": "SANTALUCIA", "cell": "C17"},
    "59.1": {"basin": "SANTALUCIA", "cell": "C7"},
    "133.0": {"basin": "SANTALUCIA", "cell": "C12"},
    "10.1": {"basin": "OLIMAR", "cell": "C2"},
    "115.0": {"basin": "SANJOSE", "cell": "C2"},
    "2235": {"basin": "URUGUAY", "cell": "C22"},
    "2232": {"basin": "URUGUAY", "cell": "C17"},
}

location_basin_mapping_precip = {
    "56": {"basin": "YI", "cell": "C21"},
    "43": {"basin": "OLIMAR", "cell": "C7"},
    "60": {"basin": "SANTALUCIA", "cell": "C22"},
    "10": {"basin": "CUAREIM", "cell": "C17"},
    "65": {"basin": "SANJOSE", "cell": "C7"},
}

location_basin_mapping_fcst = {
    "56": {"basin": "YI", "cell": "C24"},
    "43": {"basin": "OLIMAR", "cell": "C10"},
    "60": {"basin": "SANTALUCIA", "cell": "C25"},
    "10": {"basin": "CUAREIM", "cell": "C20"},
    "65": {"basin": "SANJOSE", "cell": "C10"},
}

# %%
excel_file = 'database_report.xlsx'
wb = xw.Book(excel_file)

# Water stage: latest + value 1 hour before
write_values_to_excel(wb, dfs_stage_sim, location_basin_mapping,
                      offsets=[pd.Timedelta(hours=-1)], decimals=2)

# Observed precipitation: latest + same timestamp + 1 day before
write_values_to_excel(wb, dfs_precip_sim, location_basin_mapping_precip,
                      offsets=[pd.Timedelta(days=-1), pd.Timedelta(days=-2)], decimals=0)

# Forecast precipitation: tomorrow (lead 1) + day after tomorrow (lead 2) + 3 days ahead (lead 3)
tomorrow = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)
write_values_to_excel(wb, dfs_precip_fcst, location_basin_mapping_fcst,
                      offsets=[pd.Timedelta(days=1), pd.Timedelta(days=2)], decimals=0,
                      anchor_time=tomorrow)

wb.sheets["URUGUAY"].range("C27").value = args.Q_EROGADO_SG
wb.sheets["NEGRO"].range("C12").value = args.Q_EROGADO_BONETE
wb.sheets["NEGRO"].range("C13").value = args.Q_EROGADO_PALMAR

wb.save(excel_file)
wb.close()



