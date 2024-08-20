# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Library of utils to support the WMO Pilot: Calculate Metrics notebook.

This library and the associated notebook are used to define experiments for the
Google Flood Forecasting WMO Pilot project.
"""

import numpy as np
import pandas as pd
import xarray as xr

BENCHMARK_NAMES = {
    'climatology': 'Climatology Benchmark',
    'persistence': 'Persistence Benchmark',
    'provider': 'Provider Forecasts',
    'glofas': 'GLOFAS Forecasts',
}

BENCHMARK_DESCRIPTIONS = {
    'cilmatology': 'Monthly average',
    'persistence': 'Persistence since issue time',
    'provider': 'Provider forecasts',
    'glofas': 'GLOFAS forecasts',
}


def persistence_benchmark(
    baseline_hydrographs: xr.Dataset,
) -> xr.Dataset:
  """Calculates a benchmark based on persistence since issue time.

  This benchmark is based on the observations at the issue time of a forecast.
  The forecast is simply the observation at the issue time.

  Args:
    baseline_hydrographs: A dataset containing the baseline hydrographs from
      which to extract observations at issue time. Must be indexed by time,
      lead_time, and gauge_id and have a variable called 'observation'.

  Returns:
    A dataset containing the benchmark results.
  """
  lead_time_0_obs = baseline_hydrographs.sel(
      {'lead_time': 0}
  ).observation.values
  persistence = np.transpose(
      np.tile(lead_time_0_obs, (len(baseline_hydrographs.lead_time), 1, 1)),
      (1, 2, 0),
  )
  da = xr.DataArray(
      data=persistence,
      coords={
          'gauge_id': baseline_hydrographs.gauge_id,
          'time': baseline_hydrographs.time,
          'lead_time': baseline_hydrographs.lead_time,
      },
      name='prediction',
  )
  return xr.merge([da, baseline_hydrographs.observation])


def monthly_climatology_benchmark(
    observed_hydrograph: xr.Dataset,
) -> xr.Dataset:
  """Calculates a benchmark based on monthly climatology.

  Args:
    observed_hydrograph: A dataset containing the observation hydrographs from
      which to extract cliamtologies. Must be indexed by time, lead_time, and
      gauge_id and have a variable called 'observation'.

  Returns:
    A dataset containing the benchmark results.
  """
  gauge_das = {}
  for gauge in observed_hydrograph.gauge_id.values:
    oh = observed_hydrograph.observation.sel({'lead_time': 0, 'gauge_id': gauge})
    oh['month'] = oh.time.dt.strftime('%Y-%m')
    grouped = oh.groupby('month').max()
    grouped['month'] = [int(my.split('-')[1]) for my in grouped.month.values]
    monthly_gauge_average = grouped.groupby('month').mean()
    # monthly_gauge_average = observed_hydrograph.observation.sel(
    #     {'lead_time': 0, 'gauge_id': gauge}).groupby('time.month').mean('time')
    month_das = {}
    for month in monthly_gauge_average.month.values:
      month_indexes = [
          m == month
          for m in pd.DatetimeIndex(observed_hydrograph.time.values).month
      ]
      month_times = observed_hydrograph.time[month_indexes]
      month_np = np.full(
          (
              1,
              len(month_times),
              len(observed_hydrograph.lead_time)
          ),
          monthly_gauge_average.sel({'month': month}).values
      )
      month_das[month] = xr.DataArray(
          data=month_np,
          coords={
              'gauge_id': [gauge],
              'time': month_times,
              'lead_time': observed_hydrograph.lead_time
          },
          name='prediction'
      )
    gauge_das[gauge] = xr.concat(month_das.values(), dim='time')

  benchmark = xr.concat(gauge_das.values(), dim='gauge_id')
  return xr.merge(
      [
          benchmark,
          observed_hydrograph.observation
      ]
  )
  