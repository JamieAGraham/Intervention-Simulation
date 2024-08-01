import geopandas as gpd
from shapely.geometry import Point, LineString
import numpy as np

# Load the shapefile
gdf = gpd.read_file('Geofiles\\gis_osm_roads_free_1.shp')
gdf = gdf.to_crs(epsg=27700)

# Ensure the road network is in a Linestring geometry
gdf = gdf[gdf.geometry.type == 'LineString']

# Calculate cumulative length of all roads
total_length = gdf.geometry.length.sum()

def sample_points_proportionally(line, total_length, sampling_distance):
    """Samples points at regular intervals along a LineString."""
    points = []
    current_distance = sampling_distance  # Start at the sampling distance
    while current_distance < line.length:
        point = line.interpolate(current_distance)
        points.append(point)
        current_distance += sampling_distance  # Move to the next interval
    return points

# Sample points with a fixed interval
sampling_distance = 1000  # meters (adjust as needed)
points = []
for _, row in gdf.iterrows():
    line = row.geometry
    points.extend(sample_points_proportionally(line, total_length, sampling_distance))

# Convert sampled points to a GeoDataFrame
sampled_points_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(points), crs="EPSG:27700")

# (Optional) Save the sampled points
sampled_points_gdf.to_file('sampled_points_proportional.shp')