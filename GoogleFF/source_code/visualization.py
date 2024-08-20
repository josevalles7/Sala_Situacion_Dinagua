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
"""Library of utils to support the WMO Pilot: Results Analysis notebook.

This library and the associated notebook are used to define experiments for the
Google Flood Forecasting WMO Pilot project.
"""

from typing import Mapping, Sequence, Tuple

import geopandas as gpd
import matplotlib
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import xarray as xr

import folium_utils


_DEFAULT_INITIAL_MAP_ZOOM = 8
_DEFAULT_COLOR_SCALE = 'viridis'

_AXIS_FONT_SIZE = 16
_TITLE_FONT_SIZE = 24
_TICKS_FONT_SIZE = 12
_DEFAULT_FIG_WIDTH = 20
_DEFAULT_FIG_HEIGHT = 8

# Parameters for choosing realistic map aspect ratio.
_SPHERE_RATIO = 2.05458
_LATITIDE_FIG_SCALER = 1 / _SPHERE_RATIO
_GLOBAL_GEOJSON = '../data/naturalearth_lowres.geojson'


METRICS_PLOTTING_BOUNDS = {
    'MSE': [0, 10],
    'RMSE': [0, 10],
    'NSE': [0.1, 0.9],
    'log-NSE': [0.1, 0.9],
    'Beta-NSE': [-0.2, 0.2],
    'Alpha-NSE': [0, 1.5],
    'KGE': [0.1, 0.9],
    'log-KGE': [0.1, 0.9],
    'Pearson-r': [0.3, 0.9],
    'Beta-KGE': [0, 1],
    'Peak-Timing': [0, 1],
    'Missed-Peaks': [0, 3],
    'precision': [0, 1],
    'recall': [0, 1],
}

EXPERIMENT_NAMES = {
    'gauged': 'Gauged',
    'ungauged': 'Ungauged',
    'random_cross_validation': 'Random x-Val',
    'hydrologically_separated_cross_validation': 'Hyd. x-Val',
    'persistence': 'Persistence',
    'monthly_climatology': 'Mon. Clim.',
}

DEFAULT_METRICS = [
    'NSE',
    'KGE',
    'Beta-NSE',
    'Alpha-NSE',
    '2-year-precision-1-day-window',
    '2-year-recall-1-day-window',
]


# ------------------------------------------------------------------------------
# Main functions called from notebook.
# ------------------------------------------------------------------------------
def plot_cross_validation_experiment_folium(
    splits: Mapping[str, Sequence[str]],
    geography: gpd.GeoDataFrame,
    map_center: Tuple[float, float] | None = None,
    initial_map_zoom: float = _DEFAULT_INITIAL_MAP_ZOOM,
    height: float = 1000,
    width: str = '100%',
):
  """Plot map of cross validation experiment."""
  gauges = []
  for split in splits.values():
    gauges.extend(split)

  color_cycle = [
      'red', 'blue', 'green', 'purple', 'orange', 'darkred',
      'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
      'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen',
      'gray', 'black', 'lightgray'
  ]

  if len(splits) > 1:
    color_cycle_indexes = _get_evenly_spaced_unique_integers(
        len(color_cycle), len(splits))
  else:
    color_cycle_indexes = [0]
  split_colors = {
      split: color_cycle[color_cycle_indexes[i]]
      for i, split in enumerate(splits)
  }
  gauge_colors = {
      gauge: split_colors[split]
      for split in splits
      for gauge in splits[split]
  }

  gauge_latlons = {
      gauge: (
          geography.loc[gauge, 'gauge_latitude'],
          geography.loc[gauge, 'gauge_longitude']
      )
      for gauge in gauges
  }

  basin_polygons = {
      gauge: geography.loc[gauge, 'geometry']
      for gauge in gauges
  }

  return _show_geography(
      gauge_latlons=gauge_latlons,
      basin_polygons=basin_polygons,
      initial_map_zoom=initial_map_zoom,
      map_center=map_center,
      colors=gauge_colors,
      height=height,
      width=width,
  )


def plot_cross_validation_experiment_cartoon(
    splits: Mapping[str, Sequence[str]],
    geography: gpd.GeoDataFrame,
    provider_countries: Sequence[str] | None = None,
    admin_area_geojson_path: str = _GLOBAL_GEOJSON,
):
  """Plot map of cross validation experiment."""
  # Administrative borders.
  _, ax = _init_spatial_figure_with_country_boundaries(
      admin_area_geojson_path=admin_area_geojson_path,
      provider_countries=provider_countries,
  )

  gauges = []
  for split in splits.values():
    gauges.extend(split)

  geography.loc[gauges].plot(ax=ax, linewidth=1, color='none')

  potential_colorcycles = ['Set1', 'Set2', 'tab10', 'tab20']
  potential_colorcycles = {c: 0 for c in potential_colorcycles}
  for cycle in potential_colorcycles:
    potential_colorcycles[cycle] = len(plt.cm.get_cmap(cycle).colors)
  potential_colorcycles = sorted(
      potential_colorcycles.items(), key=lambda item: item[1])

  color_cycle = None
  for pcc in potential_colorcycles:
    if pcc[1] > len(splits):
      color_cycle = pcc[0]
      break
  if color_cycle is None:
    color_cycle = plt.cm.get_cmap(potential_colorcycles[-1][0]).colors
  else:
    color_cycle = plt.cm.get_cmap(color_cycle).colors

  if len(splits) > 1:
    color_cycle_indexes = _get_evenly_spaced_unique_integers(
        len(color_cycle), len(splits))
  else:
    color_cycle_indexes = [0]
  split_colors = {
      split: color_cycle[color_cycle_indexes[i]]
      for i, split in enumerate(splits)
  }

  for split in splits:
    ax.scatter(
        geography.loc[splits[split], 'gauge_longitude'],
        geography.loc[splits[split], 'gauge_latitude'],
        s=300,
        c=split_colors[split],
    )
  plt.show()


def basin_and_gauge_geography(
    geography: gpd.GeoDataFrame,
    gauges: Sequence[str] | None = None,
    map_center: Tuple[float, float] | None = None,
    initial_map_zoom: float = _DEFAULT_INITIAL_MAP_ZOOM,
    height: float = 1000,
    width: str = '100%',
):
  """Plot the basin + gauge geography for one or more gauges.

  Creates a folium map with satellite imagery, basin polygons, and gauge
  locations. 

  Args:
    geography: GeoDataFrame containing basin polygons and gauge locations.
    gauges: List of gauges to plot. Defaults to all gauges in the dataset.
    map_center: Center of the map.
    initial_map_zoom: Initial zoom of the map.
    height: Height of the map in pixels.
    width: Width of the map as a string expressed either as a percentage of
      the width of the screen or as a number of pixels.

  Returns:
    Folium map object.
  """
  if gauges is None:
    gauges = geography.index.tolist()
  if [g for g in gauges if g not in geography.index]:
    raise ValueError('Geography is missing gauges.')

  colors = {gauge: 'blue' for gauge in gauges}
  labels = {gauge: gauge for gauge in gauges}

  gauge_latlons = {
      gauge: (
          geography.loc[gauge, 'gauge_latitude'],
          geography.loc[gauge, 'gauge_longitude']
      )
      for gauge in gauges
  }

  basin_polygons = {
      gauge: geography.loc[gauge, 'geometry']
      for gauge in gauges
  }

  return _show_geography(
      gauge_latlons=gauge_latlons,
      basin_polygons=basin_polygons,
      initial_map_zoom=initial_map_zoom,
      map_center=map_center,
      colors=colors,
      basin_labels=labels,
      gauge_labels=labels,
      height=height,
      width=width,
  )


def plot_forecast_traces(
    hydrographs: xr.Dataset,
    experiment: str,
    gauge: str,
    start_time_idx: int,
    time_window_days: int = 120,
):
    issue_times = hydrographs['time'].values
    num_lead_times = len(hydrographs['lead_time'].values)
    start_date = issue_times[start_time_idx]
    time_window = pd.Timedelta(days=time_window_days)
    plot_times_mask = (issue_times > start_date) & (issue_times < start_date + time_window) 
    issue_times = issue_times[plot_times_mask]
    ds = hydrographs.sel(
        {
            'time': issue_times,
            'experiment': experiment,
            'gauge_id': gauge,
        }

    )

    # Plot observations.
    plt.figure(figsize=(12, 6))
    obs = ds.sel(lead_time=0).observation.to_series()
    fig = px.line(obs, title=f'Gauge: {gauge}, Experiment: {experiment}')

    # Plot forecast traces.
    for i, issue_time in enumerate(issue_times):
        ds_issue = ds.sel(time=issue_time)
        lead_times = issue_times[i:i+num_lead_times]
        forecast_values = ds_issue.prediction.values
        if len(lead_times) == len(forecast_values):
          fig.add_trace(
              go.Scatter(
                  x=lead_times,
                  y=forecast_values,
                  showlegend=False
              )
          )

    # Add the time slider.
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
    fig.show()



def plot_hydrographs_for_gauge(
    hydrographs: xr.Dataset,
    gauge: str,
    experiments: Sequence[str],
    lead_time: int = 0,
):
  """Plot hydrographs for a gauge for multiple experiments.

  Args:
    hydrographs: Xarray dataset containing hydrographs.
    gauge: Gauge ID.
    lead_time: Lead time of the hydrographs.
    experiments: List of experiments to plot.
  """
  observation = (
      hydrographs.sel({
          'experiment': experiments[0],
          'gauge_id': gauge,
          'lead_time': lead_time,
      })
      .observation.to_series()
      .rename('Observation')
  )

  predictions = [
      hydrographs.sel({
          'experiment': experiment,
          'gauge_id': gauge,
          'lead_time': lead_time,
      })
      .prediction.to_series()
      .rename(EXPERIMENT_NAMES[experiment])
      for experiment in experiments
      if experiment in hydrographs.experiment.values
  ]
  predictions = pd.concat(predictions, axis=1)

  fig = px.line(predictions, title=f'Gauge: {gauge}, Lead Time: {lead_time}')
  fig.add_trace(
      go.Scatter(
          x=observation.index,
          y=observation.values,
          line=dict(color='black', dash='dot'),
          name='Observation',
      )
  )
  fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
  fig.show()


def scores_table(
    metrics: Sequence[str],
    gauge: str,
    lead_time: int,
    metrics_ds: xr.Dataset,
):
  """Plot a table of scores for a gauge and lead time.

  Args:
    metrics: List of metrics to show.
    gauge: Gauge ID.
    lead_time: Lead time of the hydrographs.
    metrics_ds: Xarray dataset containing metrics.
  """
  show_metrics = [m for m in metrics]
  gauge_metrics_ds = metrics_ds.sel(
      {
          'gauge_id': gauge,
          'lead_time': lead_time
      }
  )[show_metrics]
  df = gauge_metrics_ds.to_dataframe().transpose()
  df.drop(['lead_time', 'gauge_id'], inplace=True)
  bbox = [0, 0, 1.75, len(metrics)/5]
  df.update(df.map('{:,.3f}'.format))
  mpl_table = plt.table(
      cellText=df.values,
      rowLabels=df.index,
      bbox=bbox,
      colLabels=[EXPERIMENT_NAMES[e] for e in df.columns],
      loc='center'
  )
  plt.axis('off')
  mpl_table.auto_set_font_size(False)
  mpl_table.set_fontsize(12)
  plt.show()


def score_map(
    basin_geometries: gpd.GeoDataFrame,
    experiment: str,
    metric: str,
    metrics: xr.Dataset,
    lead_time: int,
    baseline_experiment: str | None = None,
    admin_area_geojson_path: str = _GLOBAL_GEOJSON,
    provider_countries: Sequence[str] | None = None,
    show_colorbar: bool = True,
):
  """Plot a spatial map of a particular score.

  This is a cartoon map where basin geometries are colored by metric scores.

  Args:
    basin_geometries: GeoDataFrame containing basin geometries.
    experiment: Name of the experiment to plot.
    metric: Name of the metric to plot.
    metrics: Xarray dataset containing metrics.
    lead_time: Lead time of the hydrographs.
    baseline_experiment: Name of the baseline experiment to compare with.
    admin_area_geojson_path: Path to the administrative area geojson.
    provider_countries: List of provider countries to show.
  """
  # Administrative borders.
  fig, ax = _init_spatial_figure_with_country_boundaries(
      admin_area_geojson_path=admin_area_geojson_path,
      provider_countries=provider_countries,
  )

  # Extract scores from experiment results.
  scores = metrics.sel(
      {'experiment': experiment, 'lead_time': lead_time}
  )[metric].to_series().rename(metric)
  gauges = scores.index.tolist()

  colormap = 'viridis'
  title = f'{metric}: {experiment}'
  colorbar_label = metric

  vmin = scores.min()
  vmax = scores.max()

  if baseline_experiment is not None:
    baseline_scores = metrics.sel(
        {
            'experiment': baseline_experiment,
            'gauge_id': gauges,
            'lead_time': lead_time
        }
    )[metric].to_series().rename(metric)
    scores = (scores - baseline_scores).rename(metric)
    colormap = 'PiYG'
    title = f'Δ{metric}: {experiment} - {baseline_experiment}'
    colorbar_label = f'Δ{metric}'
    vmin = scores.min()
    vmax = scores.max()
    vmax = np.max([np.abs(vmin), np.abs(vmax)])
    vmin = -vmax

  plotdata = pd.concat([scores, basin_geometries.loc[gauges]], axis=1)
  plotdata = gpd.GeoDataFrame(plotdata, geometry='geometry')
  plotdata.plot(column=metric, cmap=colormap, ax=ax, linewidth=1)

  cmap = plt.get_cmap(colormap)
  ax.scatter(
      plotdata['gauge_longitude'],
      plotdata['gauge_latitude'],
      c=plotdata[metric],
      s=50,
      vmin=vmin,
      vmax=vmax,
      cmap=cmap,
  )

  # Aesthetics.
  ax.set_title(title, fontsize=_TITLE_FONT_SIZE)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)
  ax.spines['bottom'].set_visible(False)
  ax.spines['left'].set_visible(False)
  ax.set_xticks([])
  ax.set_yticks([])

  # Colorbar.
  if show_colorbar:
    norm = Normalize(vmin=vmin, vmax=vmax)
    sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, label=metric, orientation='vertical')
    cbar.solids.set_edgecolor('face')
    cbar.set_label(None)
    cbar.set_label(colorbar_label, rotation=90, fontsize=_AXIS_FONT_SIZE)
    cbar.ax.tick_params(labelsize=_TICKS_FONT_SIZE)
  plt.show()


def score_distribution_box_plot(
    metrics: xr.Dataset,
    experiments: list[str],
    gauges: Sequence[str] | None = None,
    lead_times: Sequence[int] | None = None,
    metric: str = 'NSE',
    highlight_gauge: str | None = None,
):
  """Plot a score distribution box plot.

  Can choose between experiments, metrics, and lead times.

  Args:
    metrics: Xarray dataset containing metrics.
    experiments: List of experiments to plot. Defaults to all experiments in
      the dataset.
    gauges: List of gauges to plot. Defaults to all gauges in the dataset.
    lead_times: List of lead times to plot. Defaults to all lead times in the
      dataset.
    metric: Name of the metric to plot.
    highlight_gauge: Gauge ID to highlight.
  """

  if gauges is None:
    gauges = list(metrics.gauge_id.values)

  if lead_times is None:
    lead_times = list(metrics.lead_time.values)

  experiment_metrics_dfs = {
      experiment: metrics.sel(
          {
              'experiment': experiment,
              'lead_time': lead_times,
              'gauge_id': gauges,
          }
      )[metric].to_dataframe()
      for experiment in experiments
  }
  df = pd.concat(experiment_metrics_dfs.values(), axis=0)
  df.reset_index(inplace=True)

  _ = plt.figure(figsize=(_DEFAULT_FIG_WIDTH, _DEFAULT_FIG_HEIGHT))
  sns.boxplot(
      data=df,
      x='lead_time',
      y=metric,
      hue='experiment',
      showfliers=False
  )
  plt.xticks(fontsize=_TICKS_FONT_SIZE)
  plt.xlabel('Lead Time', fontsize=_AXIS_FONT_SIZE)
  plt.ylabel(metric, fontsize=_AXIS_FONT_SIZE)
  plt.title('Skill Score Distributions', fontsize=_TITLE_FONT_SIZE)
  plt.grid()

  if highlight_gauge is not None:
    plt.axvline(
        x=df[df['gauge_id'] == highlight_gauge]['lead_time'].values[0],
        color='red'
    )
  plt.show()
  return


def plot_cdfs(
    metrics: xr.Dataset,
    experiments: Sequence[str] | None = None,
    lead_times: Sequence[int] | None = None,
    gauges: Sequence[str] | None = None,
):
  """Plot a lead time CDF plot.

  Creates suplots for all metrucs in the metrics dataset. Traces in each subplot
  are for each experiment OR each lead time. If multiple experiments AND
  multiple lead times are supplied, will return an error.

  Args:
    metrics: Xarray dataset containing metrics.
    experiments: List of experiments to plot. Defaults to all experiments in
      the dataset.
    lead_times: List of lead times to plot. Defaults to all lead times in the
      dataset.
    gauges: List of gauges to plot. Defaults to all gauges in the dataset.
  """
  if experiments is None:
    experiments = list(metrics.experiment.values)
  if lead_times is None:
    lead_times = list(metrics.lead_time.values)
  if len(experiments) > 1 and len(lead_times) > 1:
    raise ValueError('Multiple experiments and lead times are not supported.')

  if gauges is None:
    gauges = list(metrics.gauge_id.values)
  if len(gauges) < 2:
    raise ValueError('Not enough gauges were supplied to create a CDF plot.')

  metric_names = list(set(list(metrics.variables)) - set(list(metrics.dims)))
  metric_names.sort()
  subplot_layout = _find_best_subplot_layout(len(metric_names))
  _, axes = plt.subplots(
      subplot_layout[0],
      subplot_layout[1],
      figsize=(_DEFAULT_FIG_WIDTH, _DEFAULT_FIG_HEIGHT),
  )

  def create_plotting_df_by_lead_time(
      metrics: xr.Dataset,
      experiment: str,
      lead_times: Sequence[int],
      gauges: Sequence[str],
      metric_name: str,
  ):
    df = metrics.sel(
        {
            'experiment': list(experiment[:1]),
            'gauge_id': gauges,
            'lead_time': list(lead_times)
        }
    )[metric_name].to_dataframe()
    df.reset_index(inplace=True)
    df = pd.pivot_table(
        df,
        values=[metric_name],
        columns=['lead_time'],
        index=['gauge_id']
    )
    df.columns = df.columns.droplevel(0).rename(None)
    df.rename(
        columns={col: f'lead time {col}' for col in df.columns}, inplace=True)
    return df

  def create_plotting_df_by_experiment(
      metrics: xr.Dataset,
      experiments: Sequence[str],
      lead_time: int,
      gauges: Sequence[str],
      metric_name: str,
  ):
    df = metrics.sel(
        {
            'experiment': list(experiments),
            'gauge_id': gauges,
            'lead_time': list(lead_time[:1])
        }
    )[metric_name].to_dataframe()
    df.reset_index(inplace=True)
    df = pd.pivot_table(
        df,
        values=[metric_name],
        columns=['experiment'],
        index=['gauge_id']
    )
    df.columns = df.columns.droplevel(0)
    return df

  for ax, metric in zip(axes.flatten(), metric_names):
    if len(experiments) == 1:
      df = create_plotting_df_by_lead_time(
          metrics=metrics,
          experiment=experiments,
          lead_times=lead_times,
          gauges=gauges,
          metric_name=metric,
      )
    elif len(lead_times) == 1:
      df = create_plotting_df_by_experiment(
          metrics=metrics,
          experiments=experiments,
          lead_time=lead_times,
          gauges=gauges,
          metric_name=metric,
      )
    else:
      raise ValueError('Multiple experiments and lead times are not supported.')
    if metric in METRICS_PLOTTING_BOUNDS:
      plotting_bounds = METRICS_PLOTTING_BOUNDS[metric]
    elif 'precision' in metric:
      plotting_bounds = METRICS_PLOTTING_BOUNDS['precision']
    elif 'recall' in metric:
      plotting_bounds = METRICS_PLOTTING_BOUNDS['recall']
    else:
      raise ValueError(f'Metric {metric} not found in METRICS_PLOTTING_BOUNDS')

    _plot_df_cdfs(
        df=df,
        ax=ax,
        xlabel=metric,
        xlim=plotting_bounds,
    )
    ax.grid()


# ------------------------------------------------------------------------------
# Helper functions.
# ------------------------------------------------------------------------------
# def _score_to_color(
#     score: float,
#     vmin: float,
#     vmax: float,
#     cmap: str,
# ) -> Sequence[float]:
#   norm = (score - vmin) / (vmax - vmin)
#   colormap = cm.get_cmap(cmap)
#   rgb = colormap(norm)
#   return rgb[:3]


# def _gauge_score_name_string(
#     gauge_id: str,
#     metric_name: str,
#     score: float
# ) -> str:
#   # return f'{gauge_id}: {metric_name} = {score}'.format(score)
#   return '{gauge}: {metric} = {score:.3f}'.format(
#       gauge=gauge_id, metric=metric_name, score=score)


# def _score_to_hexcolor(
#     score: float,
#     score_range: tuple[float, float],
#     colorscale: str,
# ) -> str:
#   normalized_score = (
#       score - score_range[0]) / (score_range[1] - score_range[0])
#   cmap = plt.cm.get_cmap(colorscale)
#   color = cmap(normalized_score)
#   rgb = [int(c*255) for c in color]
#   return '#{0:02x}{1:02x}{2:02x}'.format(rgb[0], rgb[1], rgb[2])


def _find_best_subplot_layout(
    total_number_of_subplots: int
) -> tuple[int, int]:
  """Finds a suitable subplot grid for a given number of subplots."""
  pseudo_factors = [(1, total_number_of_subplots)]
  while len(pseudo_factors) == 1:
    pseudo_factors = list(
        set([
            (i, total_number_of_subplots // i)
            for i in range(1, int(total_number_of_subplots**0.5) + 1)
            if total_number_of_subplots % i == 0
        ])
    )
    total_number_of_subplots += 1
  pseudo_factor_sum = [f[0]+f[1] for f in pseudo_factors]
  return pseudo_factors[np.argmin(pseudo_factor_sum)]


def _init_spatial_figure_with_country_boundaries(
    admin_area_geojson_path: str = _GLOBAL_GEOJSON,
    provider_countries: Sequence[str] | None = None,
) -> tuple[plt.Figure, plt.Axes]:
  """Initiate spatial figure with country boundaries."""

  with open(admin_area_geojson_path, 'r') as f:
    countries = gpd.read_file(f)
  countries.rename(columns={'name': 'country_name'}, inplace=True)
  countries = countries[countries['continent'] != 'Antarctica']

  if provider_countries is not None:
    gpd_row_idx = [
        i
        for i, country in enumerate(countries['country_name'])
        if country in provider_countries
    ]
    countries = countries.iloc[gpd_row_idx]

  ax = countries.boundary.plot(color='black', linewidth=2)

  fig = ax.get_figure()
  fig.set_size_inches(
      _DEFAULT_FIG_WIDTH, _LATITIDE_FIG_SCALER*_DEFAULT_FIG_WIDTH
  )
  return fig, ax


def _plot_cdf(
    scores: np.ndarray,
    ax: plt.Axes,
    label: str,
    xlabel: str,
    xlim:Tuple[float, float] | None = None,
    lw: float = 2,
    color: str = None,
    ls: str = '-',
):
  # Plot the CDF
  y_data = np.arange(1, len(scores) + 1) / float(len(scores))
  x_data = np.sort(np.squeeze(scores))
  if color is not None:
    ax.plot(x_data, y_data, label=label, lw=lw, c=color, ls=ls)
  else:
    ax.plot(x_data, y_data, label=label, lw=lw, ls=ls)

  # Aesthetics
  ax.legend()
  plt.legend(loc="upper left")
  ax.set_ylabel('Fraction of Basins', fontsize=_AXIS_FONT_SIZE)
  ax.set_xlabel(xlabel, fontsize=_AXIS_FONT_SIZE)
  if xlim is not None:
    ax.set_xlim(xlim)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)


def _plot_df_cdfs(
    df: pd.DataFrame,
    ax: plt.Axes,
    xlabel: str,
    xlim: Tuple[float, float] | None = None,
) -> tuple[plt.Axes, plt.Axes]:
  for column in df.columns:
    _plot_cdf(
        scores=df[column].values,
        ax=ax,
        label=column,
        xlabel=xlabel,
        xlim=xlim,
    )


def _show_geography(
    gauge_latlons: Mapping[str, tuple[float, float]],
    basin_polygons: Mapping[str, Sequence[str]],
    initial_map_zoom: float,
    map_center: tuple[float, float],
    colors: Mapping[str, float] | None = None,
    gauge_labels: Sequence[str] | None = None,
    basin_labels: Sequence[str] | None = None,
    height=1000,
    width='100%',
):
  """Plot the geography for a provider."""
  if any([
      gauge
      for gauge in gauge_latlons.keys()
      if gauge not in basin_polygons.keys()
  ]) or any([
      gauge
      for gauge in basin_polygons.keys()
      if gauge not in gauge_latlons.keys()
  ]):
    raise ValueError('Gauge and basin lists do not match.')

  if colors is None:
    colors = {gauge: 'blue' for gauge in gauge_latlons.keys()}
  if gauge_labels is None:
    gauge_labels = {gauge: gauge for gauge in gauge_latlons.keys()}
  if basin_labels is None:
    basin_labels = gauge_labels

  basin_map = folium_utils.make_map(
      height=height,
      width=width,
      center_lat=map_center[0],
      center_lng=map_center[1],
      zoom=initial_map_zoom,
  )

  for gauge, latlon in gauge_latlons.items():
    folium_utils.add_marker_to_map(
        longitude=latlon[1],
        latitude=latlon[0],
        map_object=basin_map,
        color=colors[gauge],
        name=gauge_labels[gauge],
    )
    folium_utils.add_polygon_to_map(
        polygon=basin_polygons[gauge],
        map_object=basin_map,
        weight=1.0,
        color=colors[gauge],
        name=basin_labels[gauge],
    )

  return basin_map


def _get_evenly_spaced_unique_integers(
    m: int,
    n: int,
) -> Sequence[int]:
  """
  Generates n evenly spaced unique integers from the range 1 to m (inclusive).

  Args:
    m: The maximum integer (inclusive).
    n: The number of integers to generate.

  Returns:
    A list of n unique, evenly spaced integers.
  """
  if n > m:
    raise ValueError("n cannot be greater than m")

  ideal_spacing = (m - 1) / (n - 1)  # Calculate ideal spacing
  adjusted_spacing = round(ideal_spacing)  # Round to nearest integer

  # Ensure spacing doesn't create duplicates at the end
  start = 0
  if start + adjusted_spacing * (n - 1) > m:
    adjusted_spacing -= 1

  # Generate the integers
  result = [start + i * adjusted_spacing for i in range(n)]
  return result
