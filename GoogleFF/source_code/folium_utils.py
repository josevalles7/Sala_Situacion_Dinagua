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

"""Simple wrappers around the folium API.

Sample usage:
```
  basin_map = folium_utils.make_map(
      height=700, center_lat=center[0], center_lng=center[1], zoom=9)

  for gauge_site in [...]:
    folium_utils.add_gauge_site_to_map(gauge_site, basin_map)

  folium_utils.add_layer_control_to_map(basin_map)

  basin_map
```
The above code displays something like this: 
* Gauges show their IDs on hover.
* Basins display their gauges and areas on click.
* Hovering on the layers icon (top-right) allows to hide a gauge and its basin.
* The tools on the left hand side allow drawing on the map.
"""

from typing import Optional, Union

import branca.element
import folium
import folium.plugins
import geopandas as gpd
import shapely.geometry

_GAUGE_COLOR = 'orange'
_SIMPLIFICATION_TOLERANCE = 0.001

BASEMAPS = {
    'map': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Maps',
        overlay=True,
        control=True,
    ),
    'satellite': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=True,
        control=True,
    ),
    'terrain': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Terrain',
        overlay=True,
        control=True,
    ),
    'hybrid': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=True,
        control=True,
    ),
    'esri': folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=True,
        control=True,
    ),
}


def make_map(
    height: int = 1000,
    width: str = '100%',
    basemap: folium.TileLayer = BASEMAPS['hybrid'],
    center_lat: float = 0,
    center_lng: float = 0,
    zoom: int = 2,
) -> folium.Map:
  """Builds a folium map.

  Args:
    height: The height of the div in pixels.
    basemap: A map tileset to use. Common ones are in `folium_utils.BASEMAPS`.
      For more: https://leaflet-extras.github.io/leaflet-providers/preview/ .
    center_lat: Latitude of the initial center of the map.
    center_lng: Longitude of the initial center of the map.
    zoom: An initial zoom level for the map, between 0 and 18.

  Returns:
    A folium Map object, that can be used to draw markers and polygons, and be
    displayed in Colab.
  """
  fig = branca.element.Figure(height=height, width=width)

  my_map = folium.Map(location=(center_lat, center_lng), zoom_start=zoom)
  my_map.add_child(basemap)
  my_map.add_child(folium.plugins.MousePosition())
  my_map.add_child(folium.plugins.MeasureControl())
  my_map.add_child(folium.plugins.Draw())
  my_map.add_child(folium.LatLngPopup())

  fig.add_child(my_map)
  return my_map


def add_layer_control_to_map(map_object: folium.Map):
  """Adds a layer control to a folium map.

  Only run this method after all other objects are added to the map!

  Args:
    map_object: The folium map.
  """
  map_object.add_child(folium.LayerControl())


def _shapely_to_folium_polygon(
    polygon: shapely.geometry.Polygon,
    color: str = 'blue',
    weight: float = 2,
    opacity: float = 0.8,
    fill_opacity: float = 0.2,
) -> folium.GeoJson:
  """Converts a shapely polygon to a folium polygon with style settings."""
  simple_polygon = polygon.simplify(tolerance=_SIMPLIFICATION_TOLERANCE)
  polygon_json = gpd.GeoSeries(simple_polygon).to_json()
  style = {
      'fillColor': color,
      'color': color,
      'weight': weight,
      'opacity': opacity,
      'fillOpacity': fill_opacity,
  }
  return folium.GeoJson(data=polygon_json, style_function=lambda _: style)


def add_polygon_to_map(
    polygon: shapely.geometry.Polygon,
    map_object: folium.Map,
    color: str = 'blue',
    weight: float = 2,
    opacity: float = 0.8,
    fill_opacity: float = 0.2,
    name: str = '',
    area: Optional[float] = None,
):
  """Plots a polygon on a folium map."""
  polygon_json = _shapely_to_folium_polygon(
      polygon, color, weight, opacity, fill_opacity
  )
  title = name
  if area is not None:
    title += f' area={area:.2f}'
  if title:
    folium.Popup(title).add_to(polygon_json)
  if name is not None:
    group = folium.FeatureGroup(f'polygon {name}')
    polygon_json.add_to(group)
    group.add_to(map_object)
  else:
    polygon_json.add_to(map_object)


def add_marker_to_map(
    longitude: float,
    latitude: float,
    map_object: folium.Map,
    name: Optional[str] = None,
    metadata: Optional[str] = None,
    color: str = 'blue',
    icon_name: str = 'info-sign',
):
  """Plots a marker on a folium map."""
  tooltip = ''
  if name is not None:
    tooltip = name
  if metadata is not None:
    tooltip += f' {metadata}'
  if not tooltip:
    tooltip = None
  icon = folium.Icon(icon=icon_name, prefix='fa', color=color)
  marker = folium.Marker(
      location=(latitude, longitude),
      tooltip=tooltip,
      icon=icon,
  )
  if name is not None:
    group = folium.FeatureGroup(f'marker {name}')
    marker.add_to(group)
    group.add_to(map_object)
  else:
    marker.add_to(map_object)
