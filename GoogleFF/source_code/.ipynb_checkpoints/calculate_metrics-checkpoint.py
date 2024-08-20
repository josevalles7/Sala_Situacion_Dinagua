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

from typing import Mapping, Sequence

import numpy as np
import os
import pandas as pd
import tqdm
import xarray as xr

import metrics


_HYDROGRAPH_RELATIVE_PATH = 'evaluation/qgis_output'


def load_model_run(
    experiment: str,
    gauge: str,
    gauge_to_model_path: Mapping[str, str],
) -> xr.Dataset:
  """Load model run for a given experiment and gauge.

  Args:
    experiment: Name of the experiment.
    gauge: Name of the gauge.
    gauge_to_model_path: Mapping from experiment name to model run directory.

  Returns:
    Xarray dataset that contains the timeseries of streamflow predictions for a
    given model run.
  """
  if gauge in gauge_to_model_path[experiment]:
    gauge_run_dir = (
        gauge_to_model_path[experiment][gauge]
        + '/'
        + _HYDROGRAPH_RELATIVE_PATH
        + '/'
        + f'{gauge}.nc'
    )
  else:
    print(
        f'Gauge: {gauge} is not in gauge_to_model_path dict for experiment'
        f' {experiment}.'
    )
    return None
  if not os.path.exists(gauge_run_dir):
    print(f'Gauge: {gauge} missing for {experiment} at {gauge_run_dir}.')
    return None
  with open(gauge_run_dir, 'rb') as f:
    model_run = xr.load_dataset(f)
  return model_run


def load_model_runs_for_experiment(
    experiment: str,
    gauges: Sequence[str],
    gauge_to_model_path: Mapping[str, str],
) -> xr.Dataset:
  """Load all model runs for a given experiment.

  Args:
    experiment: Name of the experiment.
    gauges: List of gauges to load model runs for.
    gauge_to_model_path: Mapping from experiment name to model run directory.

  Returns:
    Xarray dataset that contains the timeseries of streamflow predictions for
    all model runs in a given experiment.
  """
  gauge_xarrays = []
  print(f'Loading model runs for experiment: {experiment} ...')
  for gauge in tqdm.tqdm(gauges):
    model_run = load_model_run(
        experiment,
        gauge,
        gauge_to_model_path,
    )
    if model_run is not None:
      gauge_xarrays.append(model_run)
  hydrographs = xr.concat(gauge_xarrays, dim='gauge_id')
  hydrographs = hydrographs.drop_vars(['percentiles', 'percentile'])
  return hydrographs


def _compute_metrics_for_experiment(
    hydrographs: xr.Dataset,
) -> pd.DataFrame:
  """Compute metrics for a given experiment.

  Args:
    hydrographs: Xarray dataset that contains the timeseries of streamflow
      predictions for all model runs in a given experiment.

  Returns:
    Pandas dataframe that contains the metrics for all test gauges in a given
    experiment.
  """
  if hydrographs is None:
    return None
  gauges = hydrographs.gauge_id.values
  lead_times = hydrographs.lead_time.values
  metrics_dfs = {gauge: [] for gauge in gauges}

  for gauge in tqdm.tqdm(gauges):
    for lead_time in lead_times:
      obs = hydrographs.sel(
          {'gauge_id': gauge, 'lead_time': lead_time}).observation
      sim = hydrographs.sel(
          {'gauge_id': gauge, 'lead_time': lead_time}).prediction
      gauge_metrics = metrics.calculate_all_metrics(
          obs, sim, datetime_coord='time')
      metrics_dfs[gauge].append(pd.Series(gauge_metrics, name=lead_time))
    metrics_dfs[gauge] = pd.concat(metrics_dfs[gauge], axis=1)
  return metrics_dfs


def compute_metrics_for_all_experiments(
    hydrographs: Mapping[str, xr.Dataset]
) -> xr.Dataset:
  """Compute metrics for all experiments.

  Args:
    hydrographs: Mapping from experiment name to xarray dataset that contains
      the timeseries of streamflow predictions for all model runs in a given
      experiment.

  Returns:
    Xarray dataset that contains the metrics for all test gauges in all
    experiments. Keyed by experimen, gauge_id, and lead time, with each metric
    as a separate variable.
  """
  lead_times = hydrographs[list(hydrographs.keys())[0]].lead_time.values
  gauges = hydrographs[list(hydrographs.keys())[0]].gauge_id.values
  metrics_list = metrics.get_available_metrics()
  metrics_np = {
      metric: np.full(
          (len(hydrographs.keys()), len(gauges), len(lead_times)),
          np.nan
      ) for metric in metrics_list
  }

  for e, experiment in enumerate(hydrographs.keys()):
    print(f'Calculating metrics for experiment: {experiment} ...')
    experiment_metrics = _compute_metrics_for_experiment(
        hydrographs[experiment])
    if experiment_metrics is None:
      continue
    for g, gauge in enumerate(gauges):
      for lt, lead_time in enumerate(lead_times):
        for metric in metrics_list:
          try:
            metrics_np[metric][e, g, lt] = experiment_metrics[
                gauge].loc[metric, lead_time]
          except:
            pass

  coords = {
      'experiment': (['experiment'], list(hydrographs.keys())),
      'gauge_id': (['gauge_id'], gauges),
      'lead_time': (['lead_time'], lead_times)
  }
  metric_das = {
      metric: xr.DataArray(data=metrics_np[metric], coords=coords)
      for metric in metrics_np
  }
  return xr.Dataset(metric_das)




