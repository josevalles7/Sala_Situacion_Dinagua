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
"""Library of utils to support the WMO Pilot: Factor Analysis notebook.

This library and the associated notebook are used to define experiments for the
Google Flood Forecasting WMO Pilot project.
"""

from typing import Mapping, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import model_selection
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestRegressor
import xarray as xr


# Number of regression trees.
N_TREES = 10

# A subset of attributes to use as predictor values. This selection is mostly
# due to challenges in naming all the HydroATLAS variables, and the skill
# is not affected by removing some of the landcover class variables.
ATTRIBUTE_DESCRIPTIVE_NAMES = {
    'calculated_drain_area': 'Drain Area',
    # 'inu_pc_umn': 'Inundation Percent Min',
    # 'inu_pc_umx': 'Inundation Percent Max',
    # 'inu_pc_ult': 'Inundation Percent Long Term Maximum',
    'lka_pc_use': 'Percent Lake Area',
    # 'lkv_mc_usu': 'Lake Volume',
    'rev_mc_usu': 'Reservoir Volume',
    'ria_ha_usu': 'River Area',
    'riv_tc_usu': 'River Volume',
    'ele_mt_uav': 'Elevation',
    'slp_dg_uav': 'Slope',
    'tmp_dc_uyr': 'Air Temperature',
    'pre_mm_uyr': 'Precipitation',
    'pet_mm_uyr': 'PET',
    'aet_mm_uyr': 'AET',
    'ari_ix_uav': 'Aridity Index',
    'cmi_ix_uyr': 'Climate Moisture Index',
    'snw_pc_uyr': 'Snow Cover Extent',
    'for_pc_use': 'Forest Cover Extent',
    'crp_pc_use': 'Cropland Extent',
    'pst_pc_use': 'Pasture Extent',
    'ire_pc_use': 'Irrigated Area Extent',
    'gla_pc_use': 'Glacier Extent',
    'prm_pc_use': 'Permafrost Extent',
    'pac_pc_use': 'Protected Area Extent',
    'cly_pc_uav': 'Soil Clay Fraction',
    'slt_pc_uav': 'Soil Silt Fraction',
    'snd_pc_uav': 'Soil Sand Fraction',
    'soc_th_uav': 'Soil Organic Carbon',
    'swc_pc_uyr': 'Soil Water Content',
    'kar_pc_use': 'Karst Area Extent',
    # 'ero_kh_uav': 'Soil Erosion',
    'pop_ct_usu': 'Population Count',
    'ppd_pk_uav': 'Population Density',
    'urb_pc_use': 'Urban Area Extent',
    'nli_ix_uav': 'Nighttime Lights Index',
    # 'rdd_mk_uav': 'Road Density',
    # 'hft_ix_u93': 'Human Footprint 1993',
    # 'hft_ix_u09': 'Human Footprint 2009',
    'gdp_ud_usu': 'GDP',
    # 'latitude': 'latitude',
    # 'longitude': 'longitude',
}


def _get_basin_attributes(
    attributes_file: str,
) -> pd.DataFrame:
  """Get basin attributes from HydroATLAS."""
  with open(attributes_file, 'rt') as f:
    return pd.read_csv(f, index_col='gauge_id')


def _create_regression_data(
    attributes_file: str,
    metrics_ds: xr.Dataset,
    experiment: str,
    lead_time: int,
    metric: str,
    attribute_names: Mapping[str, str],
    baseline_experiment: str | None = None,
) -> pd.DataFrame:
  """Create a dataframe of regression data."""
  gauges = metrics_ds.gauge_id.values.tolist()
  attributes = _get_basin_attributes(attributes_file)
  attributes = attributes.loc[gauges, attribute_names.keys()]
  attributes.rename(columns=attribute_names, inplace=True)
  attributes = (attributes - attributes.mean()) / attributes.std()
  attributes.dropna(axis=1, inplace=True)

  targets = metrics_ds[metric].sel(
      {
          'lead_time': lead_time,
          'experiment': experiment
      }
  ).to_series().rename(metric)
  if baseline_experiment is not None:
    baseline = metrics_ds[metric].sel(
        {
            'lead_time': lead_time,
            'experiment': baseline_experiment
        }
    ).to_series().rename(metric)
    targets = targets - baseline

  regression_data = pd.concat(
      [attributes, targets], axis=1).dropna()

  return regression_data


def score_prediction_leave_one_out(
    attributes_file: str,
    metrics_ds: xr.Dataset,
    experiment: str,
    lead_time: int,
    metric: str,
    baseline_experiment: str | None = None,
    attribute_names: Mapping[str, str] = ATTRIBUTE_DESCRIPTIVE_NAMES,
) -> Tuple[pd.Series, pd.Series]:
  """Train and test cross-validation random forests for score prediction.

  Can predict differences between experiments by using the `baseline_experiment`
  argument.

  Uses leave-one-out cross-validation to train and test the model.

  Args:
    metrics_ds: Xarray dataset containing metrics.
    experiment: Name of the experiment to predict.
    lead_time: Lead time of the hydrographs.
    metric: Name of the metric to predict.
    baseline_experiment: Name of the baseline experiment to compare with.
    attribute_names: Mapping of attribute names to descriptive names.

  Returns:
    Pandas series of both observed and predicted scores or score differences.
  """
  regression_data = _create_regression_data(
      attributes_file=attributes_file,
      metrics_ds=metrics_ds,
      experiment=experiment,
      lead_time=lead_time,
      metric=metric,
      baseline_experiment=baseline_experiment,
      attribute_names=attribute_names,
  )

  kf = model_selection.KFold(
      n_splits=regression_data.shape[0],
      random_state=None,
      shuffle=True
  )
  regression_gauges = regression_data.index
  splits = kf.split(regression_gauges)

  x = regression_data[[col for col in regression_data.columns if col != metric]]
  y = regression_data[metric]
  y_hat = pd.Series(data=np.nan, index=regression_gauges)

  for _, (train_index, test_index) in enumerate(splits):
    # Train/test split.
    train_gauges = [regression_gauges[idx] for idx in train_index]
    test_gauges = [regression_gauges[idx] for idx in test_index]
    train_y = y.loc[train_gauges]
    train_x = x.loc[train_gauges]
    test_x = x.loc[test_gauges]

    # RF model.
    rf = RandomForestRegressor(n_estimators=N_TREES, random_state=42)
    rf.fit(train_x, train_y)

    # Predictions.
    y_hat.loc[test_gauges] = rf.predict(test_x)

  return y_hat, y


def score_prediction_factor_analysis(
    attributes_file: str,
    metrics_ds: xr.Dataset,
    experiment: str,
    lead_time: int,
    metric: str,
    baseline_experiment: str | None = None,
    attribute_names: Mapping[str, str] = ATTRIBUTE_DESCRIPTIVE_NAMES,
) -> pd.Series:
  """Calculate factor importances from trained RF model.

  Can predict differences between experiments by using the `baseline_experiment`
  argument.

  Uses all gauges to train a single model.

  Args:
    metrics_ds: Xarray dataset containing metrics.
    experiment: Name of the experiment to predict.
    lead_time: Lead time of the hydrographs.
    metric: Name of the metric to predict.
    baseline_experiment: Name of the baseline experiment to compare with.
    attribute_names: Mapping of attribute names to descriptive names.

  Returns:
    Pandas series of factor importances.
  """
  regression_data = _create_regression_data(
      attributes_file=attributes_file,
      metrics_ds=metrics_ds,
      experiment=experiment,
      lead_time=lead_time,
      metric=metric,
      baseline_experiment=baseline_experiment,
      attribute_names=attribute_names,
  )
  x = regression_data[[col for col in regression_data.columns if col != metric]]
  y = regression_data[metric]
  rf = RandomForestRegressor()
  rf.fit(x, y)
  importances = pd.Series(
      index=x.columns,
      data=rf.feature_importances_
  ).sort_values(ascending=False)
  return importances


def plot_predicted_skill_scatter(
    y: pd.Series,
    y_hat: pd.Series,
    metric: str,
    experiment: str,
    baseline_experiment: str | None = None,
):
  title = f'{metric} for "{experiment}"'
  if baseline_experiment is not None:
    title += f' vs "{baseline_experiment}"'
  r2 = r2_score(y, y_hat)
  title += f' (R^2={r2:.2f})'

  plt.scatter(y, y_hat)
  ax = plt.gca()
  x_min, x_max = ax.get_xlim()
  y_min, y_max = ax.get_ylim()
  ax_min = min(x_min, y_min)
  ax_max = max(x_max, y_max)
  plt.grid()
  plt.axis([ax_min, ax_max, ax_min, ax_max])
  plt.plot([ax_min, ax_max], [ax_min, ax_max], 'k--')
  plt.title(title)
  plt.xlabel(f'Observed {metric}')
  plt.ylabel(f'Predicted {metric}')
  plt.show()


def plot_feature_importances(
    importances: pd.Series,
    metric: str,
    experiment: str,
    baseline_experiment: str | None = None,
):
  """Plot feature importances from trained RF model."""
  title = f'Feature Importances for {metric} in "{experiment}"'
  if baseline_experiment is not None:
    title += f' vs "{baseline_experiment}"'

  _ = plt.figure(figsize=(20, 8))
  plt.bar(importances.index, importances.values)
  plt.title(title)
  plt.ylabel('Mean Decrease in Impurity')
  plt.grid()
  ax = plt.gca()
  ax.set_xticks(
      range(len(importances.index)),
      importances.index,
      rotation=60,
      ha='right',
  )
  ax.set_yticklabels(
      ax.get_yticklabels(),
  )
