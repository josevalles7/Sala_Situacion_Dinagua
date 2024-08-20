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
"""Library of utils to support the WMO Pilot: Experiment Definition notebook.

This library and the associated notebook are used to define experiments for the
Google Flood Forecasting WMO Pilot project.
"""

from typing import Mapping, Sequence, Tuple

import geopandas as gpd
import pandas as pd
from sklearn import model_selection



# ------------------------------------------------------------------------------
# GAUGE GROUP UTILITIES
# ------------------------------------------------------------------------------
ADMIN_AREA_GEOJSON_PATH = '/cns/iz-d/home/hydro_model/gsnearing/global_model_paper/metadata/naturalearth_lowres.geojson'
TEST_GAUGE_GROUP_NAME = 'all_gauges'


def get_global_model_training_gauge_group_without_provider_country(
    gauge_group_file_path: str,
) -> Sequence[str]:
  """Remove gauges from the same country(ies) as the provider.

  Args:
    gauge_group_file_path: File containing the full training gauge group for the Google global model.
 
  Returns:
    List of gauges after filtering.
  """
  # Get global gauge group. This should be the gauge group that the current
  # production model is trained on.
  with open(gauge_group_file_path, 'rt') as f:
    return [gauge.split('/n') for gauge in f.readlines()][0]

#   print(
#       f'There are {len(global_gauge_group)} gauges in the global model training'
#       ' set.'
#   )

#   # Load attributes.
#   with open(attributes_file, 'rt') as f:
#     attributes = pd.read_csv(f, index_col='gauge_id')
#   attributes = attributes['GAUGE_DETAILS:longitude', 'GAUGE_DETAILS:latitude']

#   # Load country polygons.
#   with open(ADMIN_AREA_GEOJSON_PATH, 'r') as f:
#     countries = gpd.read_file(f)
#   countries.rename(columns={'name': 'country_name'}, inplace=True)
#   countries = countries[countries['continent'] != 'Antarctica']
#   countries.set_index('country_name', inplace=True)

#   # Find countries for all gauges.
#   gauge_country = pd.Series(index=global_gauge_group, name='country')
#   for gauge in attributes.index:
#     gauge_point = gpd.points_from_xy(
#         [attributes.loc[gauge, 'GAUGE_DETAILS:longitude']],
#         [attributes.loc[gauge, 'GAUGE_DETAILS:latitude']]
#     )
#     for country in countries.index:
#       if gauge_point.within(countries.loc[country, 'geometry']):
#         gauge_country[gauge] = country
#         break

#   # Remove gauges from the same country(ies) as the provider.
#   gauges_to_remove = gauge_country.iloc[
#       [idx for idx, gc in enumerate(gauge_country) if gc in countries_to_remove]
#   ].index
#   return [
#       g for g in global_gauge_group if g not in gauges_to_remove
#   ]


def create_gauged_run_gauge_groups(
    global_gauges: Sequence[str],
    train_gauges: Sequence[str],
    test_gauges: Sequence[str],
) -> Tuple[Sequence[str], Sequence[str]]:
  """Create train and test gauge groups for a fully gauged run.

  Args:
    global_gauges: List of gauges that are used to train the global model.
    train_gauges: List of gauges that are used in the partner training set.
    test_gauges: List of gauges that are used in the partner test set.

  Returns:
    train_gauge_group: List of gauges that are used to train the partner model.
    test_gauge_group: List of gauges that are used to test the partner model.
  """
  train_gauge_group = global_gauges + train_gauges
  test_gauge_group = test_gauges
  return train_gauge_group, test_gauge_group


def create_ungauged_run_gauge_groups(
    global_gauges: Sequence[str],
    test_gauges: Sequence[str],
) -> Tuple[Sequence[str], Sequence[str]]:
  """Create train and test gauge groups for a fully gauged run.

  Args:
    global_gauges: List of gauges that are used to train the global model.
    test_gauges: List of gauges that are used in the partner test set.

  Returns:
    train_gauge_group: List of gauges that are used to train the partner model.
    test_gauge_group: List of gauges that are used to test the partner model.
  """
  train_gauge_group = global_gauges
  test_gauge_group = test_gauges
  return train_gauge_group, test_gauge_group


def create_random_cross_validation_gauge_groups(
    global_gauges: Sequence[str],
    train_gauges: Sequence[str],
    num_cross_validation_folds: int,
) -> Tuple[Sequence[str], Sequence[str]]:
  """Create train and test gauge groups for a random cross validation run.

  Args:
    global_gauges: List of gauges that are used to train the global model.
    train_gauges: List of gauges that are used in the partner training set.
    num_cross_validation_folds: Number of cross validation folds.

  Returns:
    train_gauge_groups: Mapping from cross validation fold name to sequence of
      gauges that are used to train the partner model.
    test_gauge_groups: Mapping from cross validation fold name to sequence of
      gauges that are used to test the partner model.
  """
  k_folds = model_selection.KFold(
      n_splits=num_cross_validation_folds,
      shuffle=True
  )
  train_gauge_groups = {}
  test_gauge_groups = {}
  for fold, (train_index, test_index) in enumerate(k_folds.split(train_gauges)):
    train_gauge_groups[f'fold_{fold}'] = global_gauges + [
        train_gauges[idx] for idx in train_index]
    test_gauge_groups[f'fold_{fold}'] = [
        train_gauges[idx] for idx in test_index]
  return train_gauge_groups, test_gauge_groups


def create_hydrography_separated_cross_validation_gauge_groups(
    global_gauges: Sequence[str],
    train_gauges: Sequence[str],
    graph_crossval_split_to_gauge_mapping: Mapping[str, Sequence[str]],
) -> Tuple[Sequence[str], Sequence[str]]:
  """Create train and test gauge groups for a hydrography separated cross validation run.

  Args:
    global_gauges: List of gauges that are used to train the global model.
    train_gauges: List of gauges that are used in the partner training set.
    graph_crossval_split_to_gauge_mapping: Mapping from cross validation split
      name to sequence of gauges that are used to train the partner model.

  Returns:
    train_gauge_groups: Mapping from cross validation fold name to sequence of
      gauges that are used to train the partner model.
    test_gauge_groups: Mapping from cross validation fold name to sequence of
      gauges that are used to test the partner model.
  """
  train_gauge_groups = {}
  test_gauge_groups = {}
  for crossval_split, gauges in graph_crossval_split_to_gauge_mapping.items():
    train_gauge_groups[f'fold_{crossval_split}'] = global_gauges + [
        g for g in train_gauges if g not in gauges]
    test_gauge_groups[f'fold_{crossval_split}'] = gauges
  return train_gauge_groups, test_gauge_groups


def get_gauge_group_name(
    experiment: str,
    provider: str,
    split: str | None = None,
) -> str:
  """Name of a gauge group for a given cross-validation experiment and split."""
  if split is not None:
    return f'{provider}_{experiment}_{split}'
  else:
    return f'{provider}_{experiment}'


def get_gauge_group_path(
    experiment: str,
    provider: str,
    base_path: str,
    split: str | None = None,
) -> str:
  """File path for a given gauge group."""
  gauge_group_name = get_gauge_group_name(
      experiment=experiment,
      split=split,
      provider=provider
  )
  return f'{base_path}/{gauge_group_name}.txt'


def model_path_for_gauge_group(
    experiment: str,
    base_model_run_directory: str,
    split: str | None = None,
) -> str:
  """Model run for a given cross validation experiment and split."""
  if split is not None:
    return f'{base_model_run_directory}/{experiment}/{split}'
  else:
    return f'{base_model_run_directory}/{experiment}'


def save_all_experiment_gauge_groups_as_text_files(
    experiment_train_gauge_groups: Mapping[
        str, Sequence[str] | Mapping[str, Sequence[str]]
    ],
    provider: str,
    base_path: str,
):
  """Save all experiment gauge groups as text files.

  Args:
    experiment_train_gauge_groups: Mapping from experiment name to train gauge
      groups. This can be either a mapping from an experiment name (str) to a
      list of gauges (Sequence[str]) or a mapping from an experiment name (str)
      to a mapping from a split name (str) to a list of gauges (Sequence[str]).
    provider: Name of the provider.
    base_path: Base path to save the gauge groups.
  """
  for experiment, gauges_or_split in experiment_train_gauge_groups.items():
    if isinstance(gauges_or_split, Mapping):
      for split, gauges in gauges_or_split.items():
        gauge_group_file = get_gauge_group_path(
            experiment=experiment,
            provider=provider,
            base_path=base_path,
            split=split
        )
        with open(gauge_group_file, 'wt') as f:
          f.write('\n'.join(sorted(gauges)))
    else:
      gauge_group_file = get_gauge_group_path(
          experiment=experiment,
          provider=provider,
          base_path=base_path,
      )
      with open(gauge_group_file, 'wt') as f:
        f.write('\n'.join(sorted(gauges_or_split)))


def save_test_gauge_group_as_text_file(
    test_gauges: Sequence[str],
    provider: str,
    base_path: str,
):
  """Save test gauge group as text file.

  Args:
    test_gauges: List of gauges that are used in the partner test set.
    provider: Name of the provider.
    base_path: Base path to save the gauge groups.
  """
  test_gauge_group_file = get_gauge_group_path(
      experiment=TEST_GAUGE_GROUP_NAME,
      provider=provider,
      base_path=base_path,
  )
  with open(test_gauge_group_file, 'wt') as f:
    f.write('\n'.join(sorted(test_gauges)))


def create_test_gauge_to_model_path_mapping(
    all_test_gauges: Sequence[str],
    experiment_test_gauge_groups: Mapping[
        str, Sequence[str] | Mapping[str, Sequence[str]]
    ],
    base_path: str,
) -> Mapping[str, Mapping[str, str]]:
  """Creates a mapping from experiment name to model path for all test gauges.

  This allows us to know which model run to load for a given experiment and
  gauge.

  Args:
    all_test_gauges: List of all test gauges.
    experiment_test_gauge_groups: Mapping from experiment name to test gauge
      groups. This can be either a mapping from an experiment name (str) to a
      list of gauges (Sequence[str]) or a mapping from an experiment name (str)
      to a mapping from a split name (str) to a list of gauges (Sequence[str]).
    base_path: Base path to the model runs.

  Returns:
    Mapping from experiment name to model path for all test gauges.
  """
  gauge_to_model_path = {
      experiment: {gauge: None for gauge in all_test_gauges}
      for experiment in experiment_test_gauge_groups.keys()
  }
  for experiment, gauges_or_split in experiment_test_gauge_groups.items():
    if isinstance(gauges_or_split, Mapping):
      for split, gauges in gauges_or_split.items():
        model_path = model_path_for_gauge_group(
            experiment=experiment,
            base_model_run_directory=base_path,
            split=split
        )
        for gauge in gauges:
          gauge_to_model_path[experiment][gauge] = model_path
    else:
      model_path = model_path_for_gauge_group(
          experiment=experiment,
          base_model_run_directory=base_path,
      )
      for gauge in gauges_or_split:
        gauge_to_model_path[experiment][gauge] = model_path

  return gauge_to_model_path
# ------------------------------------------------------------------------------
# GAUGE GROUP UTILITIES
# ------------------------------------------------------------------------------


