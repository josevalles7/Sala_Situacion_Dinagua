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
# limitations under the License.\
"""Utilities to calculate return period metrics."""
from typing import Tuple

import numpy as np
import pandas as pd
import tqdm
import xarray

import exceptions
import return_period_calculator

RETURN_PERIOD_TIME_WINDOWS = [
    pd.Timedelta(0, unit='d'),
    pd.Timedelta(1, unit='d'),
    pd.Timedelta(2, unit='d'),
]

RETURN_PERIODS = [1.01, 2.0, 5.0, 10.0]


def _true_positives_fraction_in_window(
    a_crossovers: np.ndarray,
    b_crossovers: np.ndarray,
    discard_nans_in_window: bool,
    window_in_timesteps: int,
) -> float:
    """Calculates fraction of crossovers that were hit within a window.

    Handles NaNs by ignoring crossovers where array b is NaN anywhere
    within the window around crossovers in array a.

    Args:
    a_crossovers: np.ndarray
      First 0/1/NaN indicator array of crossovers.
    b_crossovers: np.ndarray
      Second 0/1/NaN indicator array of crossovers.
    discard_nans_in_window: bool
      True if you want to throw out all samples from 'a' where 'b' has any nans
        in the window.
      This is useful when 'b' are observations and you don't want to penalize a
        model due to
      the fact that the observed record is incomplete.
    window_in_timesteps: int
      Window around a crossover in a to search for a crossover in b.

    Returns:
    Fraction of crossovers in a where (1) the corresponding window in b contains
    no NaNs and (2) a corresponding crossover exists in b.
    """
    a_crossover_idxs = np.where(
        (a_crossovers != 0) & ~np.isnan(a_crossovers))[0]
    b_crossover_idxs = np.where(
        (b_crossovers != 0) & ~np.isnan(b_crossovers))[0]
    b_nan_crossover_idxs = np.where(np.isnan(b_crossovers))[0]

    # Count fraction of crossovers we hit.
    total_count = 0
    true_positives = 0
    for a_idx in a_crossover_idxs:
      # Do not count crossovers if there are NaNs in b within the window.
      if discard_nans_in_window and np.any(
          np.abs(b_nan_crossover_idxs - a_idx) <= window_in_timesteps + 1e-6
      ):
        continue
      total_count += 1
      if np.any(
          np.abs(b_crossover_idxs - a_idx) <= window_in_timesteps + 1e-6):
        true_positives += 1

    if total_count > 0:
      return true_positives / total_count

    # This is a decision to define:
    #  -- Precision as 0 if there are no predicted events but there are obsreved
    #     events.
    #  -- Recall as 0 if there are no observed events but there are predicted
    #     events.
    elif len(a_crossover_idxs) == 0 and len(b_crossover_idxs) > 0:
      return 0

    # This is a decision to define both precision and recall as 1 if there are
    # no events to predict *and* the model predicts no events.
    elif len(a_crossover_idxs) == 0 and len(b_crossover_idxs) == 0:
      return 1

    # This is a decision to define:
    #  -- Precision as 1 there are no observed data around any perdicted event.
    #  -- Recall as 1 if there are no predicted data around any observed event.
    # The second option should !not! be used. When the 'a' series are
    # observations, (i.e., calculating recall), you should set
    # `discard_nans_in_window` to False.
    elif len(a_crossover_idxs) > 0 and discard_nans_in_window:
      return 1

    else:
      print(
          total_count,
          true_positives,
          len(a_crossover_idxs),
          len(b_crossover_idxs)
      )
      print('You should only get here if there are nans in your predictions. '
            'If you see this message, please debug.')
      return np.nan


def _single_return_period_performance_metric(
    observations: np.ndarray,
    simulations: np.ndarray,
    obs_return_period_calculator: return_period_calculator.ReturnPeriodCalculator,
    sim_return_period_calculator: return_period_calculator.ReturnPeriodCalculator,
    return_period: float,
    window_in_timesteps: int,
) -> Tuple[float, float]:
  """Calculates hit/miss rates for a single return period and time window."""

  # Calculate flow values at return period. These can be different for obs and
  # sim, and we want to test based on the model climatology.
  if sim_return_period_calculator:
    sim_flow_value = sim_return_period_calculator.flow_value_from_return_period(
        return_period
    )
  else:
    sim_flow_value = np.nan
  if obs_return_period_calculator:
    obs_flow_value = obs_return_period_calculator.flow_value_from_return_period(
        return_period
    )
  else:
    return {'precision': np.nan, 'recall': np.nan}, sim_flow_value

  # Find obs points crossing return period threshold.
  above_threshold = np.where(
      np.isnan(observations),
      np.nan,
      (observations >= obs_flow_value).astype(float),
  )
  obs_crossovers = np.maximum(0, np.diff(above_threshold))

  # Find sim points crossing return period threshold.
  above_threshold = np.where(
      np.isnan(simulations),
      np.nan,
      (simulations >= sim_flow_value).astype(float),
  )
  sim_crossovers = np.maximum(0, np.diff(above_threshold))

  precision = _true_positives_fraction_in_window(
      sim_crossovers, obs_crossovers, True, window_in_timesteps
  )

  recall = _true_positives_fraction_in_window(
      obs_crossovers, sim_crossovers, False, window_in_timesteps
  )

  return precision, recall


def _prepare_hydrograph(
    hydrograph: pd.Series, temporal_resolution: pd.Timedelta
) -> pd.Series:

  hydrograph.index = [
      pd.to_datetime(t, unit='s', origin='unix') for t in hydrograph.index
  ]

  # Fill any missing dates in the datetime index. This is necessary so that
  # the window of separation is in constant units.
  new_date_range = pd.date_range(
      start=min(hydrograph.index),
      end=max(hydrograph.index),
      freq=temporal_resolution,
  )

  # Remove any duplicate timestamps and reindex so that the return period
  # calculator has a full timeseries to work with.
  hydrograph = hydrograph[~hydrograph.index.duplicated(keep='first')]
  hydrograph = hydrograph.reindex(new_date_range, fill_value=np.nan)

  return hydrograph


def construct_return_period_metric_name(
    metric_type: str,
    return_period: float,
    window: int,
) -> str:
  """Constructs a name for a return period metric.

  This metric name contains the information about the metric type, the return
  period, and the window of separation.

  Args:
    metric_type: str
      The type of metric. Must be 'precision' or 'recall'.
    return_period: float
      The return period of the event.
    window: int
      The window of separation between the observed and simulated events.

  Returns:
    A string containing the metric name.
  """
  if metric_type.lower() not in ['precision', 'recall']:
    raise ValueError(
        f'Unsupported metric type for return period metrics: {metric_type}')
  return f'{int(return_period)}-year-{metric_type}-{window}-day-window'


def deconstruct_return_period_metric_name(
    metric: str,
) -> tuple[str, int, int]:
  """Deconstructs a return period metric name into its components.

  This metric name contains the information about the metric type, the return
  period, and the window of separation.

  Args:
    metric: The name of the metric.

  Returns:
    A tuple containing the metric type, the return period, and the window of
    separation.
  """
  return_period, _, metric_type, window, _, _ = metric.split('-')
  if int(return_period) == 1:
    return_period = 1.01
  window = pd.Timedelta(int(window), unit='d')
  return metric_type, return_period, window


def metrics_for_one_gague(
    ds: xarray.Dataset,
    return_periods: list[float],
    return_period_time_windows: list[pd.Timedelta],
    temporal_resolution: pd.Timedelta,
    gauge: str,
    experiment: str,
) -> xarray.Dataset:
  """Calculates return period metrics for one gauge."""

  lead_times = ds.lead_time.values
  precision_np = np.full(
      (
          1,
          1,
          len(lead_times),
          len(return_periods),
          len(return_period_time_windows)
      ),
      np.nan
  )
  recall_np = np.full(
      (
          1,
          1,
          len(lead_times),
          len(return_periods),
          len(return_period_time_windows)
      ),
      np.nan
  )

  obs_return_period_calculator = None
  sim_return_period_calculator = None
  for lead_time_index, lead_time in enumerate(lead_times):
    predictions = _prepare_hydrograph(
        ds.sel(lead_time=lead_time).prediction.to_series(),
        temporal_resolution
    )
    observations = _prepare_hydrograph(
        ds.sel(lead_time=lead_time).observation.to_series(),
        temporal_resolution
    )

    if not obs_return_period_calculator:
      try:
        obs_return_period_calculator = (
            return_period_calculator.ReturnPeriodCalculator(
                hydrograph_series=observations,
                hydrograph_series_frequency=temporal_resolution,
                use_simple_fitting=True,
                verbose=False,
            )
        )
      except exceptions.NotEnoughDataError:
        obs_return_period_calculator = None
    if not sim_return_period_calculator:
      try:
        sim_return_period_calculator = (
            return_period_calculator.ReturnPeriodCalculator(
                hydrograph_series=predictions,
                hydrograph_series_frequency=temporal_resolution,
                use_simple_fitting=True,
                verbose=False,
            )
        )
      except exceptions.NotEnoughDataError:
        sim_return_period_calculator = None

    # Calculate the metrics.
    if obs_return_period_calculator and sim_return_period_calculator:
      for return_period_index, return_period in enumerate(return_periods):
        for window_index, window in enumerate(return_period_time_windows):
          precision, recall = _single_return_period_performance_metric(
              observations=observations.values,
              simulations=predictions.values,
              obs_return_period_calculator=obs_return_period_calculator,
              sim_return_period_calculator=sim_return_period_calculator,
              return_period=return_period,
              window_in_timesteps=window / temporal_resolution,
          )
          precision_np[
              0, 0, lead_time_index, return_period_index, window_index
          ] = precision
          recall_np[
              0, 0, lead_time_index, return_period_index, window_index
          ] = recall

  precision_das = []
  recall_das = []
  for r, return_period in enumerate(return_periods):
    for w, window in enumerate(return_period_time_windows):
      precision_das.append(
          xarray.DataArray(
              data=precision_np[:, :, :, r, w],
              coords={
                  'experiment': [experiment],
                  'gauge_id': [gauge],
                  'lead_time': lead_times,
              },
              name=construct_return_period_metric_name(
                  return_period=return_period,
                  window=window.days,
                  metric_type='precision',
              ),
          )
      )
      recall_das.append(
          xarray.DataArray(
              data=recall_np[:, :, :, r, w],
              coords={
                  'experiment': [experiment],
                  'gauge_id': [gauge],
                  'lead_time': lead_times,
              },
              name=construct_return_period_metric_name(
                  return_period=return_period,
                  window=window.days,
                  metric_type='recall',
              ),
          )
      )
  precision_ds = xarray.merge(precision_das)
  recall_ds = xarray.merge(recall_das)
  return precision_ds, recall_ds


# --- Main function to call from notebooks ----------------------------------


def compute_metrics(
    ds: xarray.Dataset,
    experiment: str
) -> list[str]:
  """Call this function to compute return period metrics for an experiment."""

  precision_das = {}
  recall_das = {}
  for gauge in tqdm.tqdm(ds.gauge_id.values):
    precision_das[gauge], recall_das[gauge] = metrics_for_one_gague(
        ds.sel(gauge_id=gauge),
        return_periods=RETURN_PERIODS,
        return_period_time_windows=RETURN_PERIOD_TIME_WINDOWS,
        temporal_resolution=pd.Timedelta(1, unit='d'),
        gauge=gauge,
        experiment=experiment,
    )

  return xarray.merge(
      [
          xarray.concat(precision_das.values(), dim='gauge_id'),
          xarray.concat(recall_das.values(), dim='gauge_id'),
      ]
  )