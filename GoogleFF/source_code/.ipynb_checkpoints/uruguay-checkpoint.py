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
"""Metadata for Uruguay."""

import os

# ------------------------------------------------------------------------------
# PARTNER METADATA
# ------------------------------------------------------------------------------
# Prefix for gauge IDs from this provider.
PREFIX = 'DNAUY'

# Information needed to make nice figures.
MAP_CENTER = (-29.65, -53.9325)
MAP_ZOOM = 6.3
COUNTRIES = ['Uruguay']

NUM_CROSS_VALIDATION_FOLDS = 6
# ------------------------------------------------------------------------------
# PARTNER METADATA
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# DATA PATHS
# ------------------------------------------------------------------------------
WORKING_DIRECTORY = '/home/gsnearing/data'

# Path to the raw data supplied by the provider.
PROVIDER_DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, 'DNAUY_provider_data')

# Path to our internal shapefiles used to extract forcing data and catchment
# attributes.
SHAPEFILE_PATH = '/home/gsnearing/data/gauge_basins_lev12.geojson'

# Path to our internal gauge information file from ingesting the streamflow
# data
GAUGE_INFO_PATH = '/home/gsnearing/data/gauges_info_lev12.csv'

# Path to gauge groups created for the experiments for this provider.
CNS_GAUGE_GROUP_PATH = WORKING_DIRECTORY + '/gauge_groups'
if not os.path.exists(CNS_GAUGE_GROUP_PATH):
  os.makedirs(CNS_GAUGE_GROUP_PATH)

# Path to our model runs for experiments for this provider.
MODEL_RUN_DIRECTORY = '/cns/jn-d/home/floods/hydro_model/work/gsnearing/wmo_pilot/uruguay/model_runs_4_1'

# Path to the consolidated experimental results.
EXPERIMENT_RESULTS_PATH = os.path.join(WORKING_DIRECTORY, 'results')
if not os.path.exists(EXPERIMENT_RESULTS_PATH):
  os.makedirs(EXPERIMENT_RESULTS_PATH)

GAUGE_TO_MODEL_PATH_MAPPING_FILE = os.path.join(
    EXPERIMENT_RESULTS_PATH, 'gauge_to_model_path_mapping.json')
# ------------------------------------------------------------------------------
# DATA PATHS
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# GAUGE GROUPS
# ------------------------------------------------------------------------------
# --- Hydrography Separated Cross-Validation Experiment
GRAPH_CROSSVAL_SPLIT_TO_GAUGE_MAPPING = {
    '52': ['DNAUY_52', 'DNAUY_1743'],
    '46_1': ['DNAUY_46.1', 'DNAUY_174'],
    '44': ['DNAUY_44', 'DNAUY_59.1', 'DNAUY_133', 'DNAUY_53.1'],
    '28': ['DNAUY_28.0', 'DNAUY_26676'],
    '2215': ['DNAUY_2215', 'DNAUY_2206', 'DNAUY_2257'],
    '14': ['DNAUY_14', 'DNAUY_15'],
    '71_0': ['DNAUY_71.0'],
    '97': ['DNAUY_97'],
    '10_1': ['DNAUY_10.1'],
    '176_1': ['DNAUY_176.1'],
}

# --- Provider Gauges ----------------------------------------------------------
TRAIN_GAUGES = []
for _, values in GRAPH_CROSSVAL_SPLIT_TO_GAUGE_MAPPING.items():
  TRAIN_GAUGES.extend(values)
TEST_GAUGES = TRAIN_GAUGES
# ------------------------------------------------------------------------------
# GAUGE GROUPS
# ------------------------------------------------------------------------------

