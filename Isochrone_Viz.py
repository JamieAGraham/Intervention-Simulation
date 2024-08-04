import geopandas as gpd
import pandas as pd
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from travel_time_calc import TravelTimeCalculator
import numpy as np

points_gdf = gpd.read_file("Geofiles/sampled_points_proportional.shp").to_crs("EPSG:4326")
results_df = pd.read_csv("travel_times_distances.csv")
calculator = TravelTimeCalculator(
        "Geofiles/sampled_points_proportional.shp", "travel_times_distances.csv"
    )

isochrone_source = (-0.218273, 51.786675)  # Example source coordinates

# Calculate travel times from source

points_gdf["travel_time_from_source"] = points_gdf.apply(
    lambda row: calculator.get_travel_time_and_distance(
        isochrone_source, np.array(row["geometry"])
    )[1],
    axis=1,
)

points = points_gdf["geometry"].to_crs("EPSG:4326")
x = points.x.values
y = points.y.values
z = points_gdf["travel_time_from_source"].values


xmin, ymin, xmax, ymax = points_gdf.total_bounds
grid_x, grid_y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]

# Interpolate travel times onto grid
travel_time_grid = griddata(
    list(zip(x, y)),
    z,
    (grid_x, grid_y),
    method="linear",
)

# Create contour plot

fig, ax = plt.subplots()
contour = ax.contourf(
    grid_x, grid_y, travel_time_grid, levels=[300, 600, 900], cmap="YlOrRd"
)
plt.colorbar(contour, label="Travel Time (seconds)")
ax.set_title("Isochrones from Source")
# ... (plot roads, points, etc. as needed)
plt.show()