import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import numpy as np


class TravelTimeCalculator:
    def __init__(self, points_file, results_file):
        """Loads and preprocesses data upon initialization."""
        self.points_gdf = gpd.read_file(points_file)
        self.results_df = pd.read_csv(results_file)
        print(self.results_df.head())
        # Precalculate squared distances for efficiency
        self.points_np = np.array(
            [p.coords[0] for p in self.points_gdf["geometry"]]
        )

    def get_travel_time_and_distance(self, origin_coords, dest_coords):
        """
        Calculates travel time and distance using nearest sampled points.

        Args:
            origin_coords: Tuple (longitude, latitude) of the origin point.
            dest_coords: Tuple (longitude, latitude) of the destination point.

        Returns:
            Tuple (distance_meters, duration_seconds), or (None, None) if not found.
        """

        # Ensure correct projection
        origin_point = (
            gpd.GeoSeries([Point(*origin_coords)])
            .set_crs("EPSG:4326")
            .to_crs(self.points_gdf.crs)[0]
        )
        dest_point = (
            gpd.GeoSeries([Point(*dest_coords)])
            .set_crs("EPSG:4326")
            .to_crs(self.points_gdf.crs)[0]
        )

        # Find nearest sampled points using NumPy for speed
        origin_np = np.array(origin_point)
        dest_np = np.array(dest_point)
        origin_distances_sq = np.sum((self.points_np - origin_np) ** 2, axis=1)
        dest_distances_sq = np.sum((self.points_np - dest_np) ** 2, axis=1)
        nearest_origin_index = np.argmin(origin_distances_sq)
        nearest_dest_index = np.argmin(dest_distances_sq)

        # Look up travel time and distance
        result = self.results_df.loc[
            (self.results_df["point1_index"] == nearest_origin_index)
            & (self.results_df["point2_index"] == nearest_dest_index)
        ]
        if not result.empty:
            return (
                result["distance_metres"].values[0],
                result["duration_seconds"].values[0],
            )

        result = self.results_df.loc[
            (self.results_df["point2_index"] == nearest_origin_index)
            & (self.results_df["point1_index"] == nearest_dest_index)
        ]
        if not result.empty:
            return (
                result["distance_metres"].values[0],
                result["duration_seconds"].values[0],
            )

        return None, None  # No matching entry found
    

# Usage in another script:
if __name__ == "__main__":
    calculator = TravelTimeCalculator(
        "Geofiles/sampled_points_proportional.shp", "travel_times_distances.csv"
    )

    origin = (-0.218273, 51.786675)  # Example origin coordinates (lon, lat)
    destination = (-0.204663, 51.899684)  # Example destination coordinates

    distance, duration = calculator.get_travel_time_and_distance(origin, destination)

    if distance is not None:
        print(f"Distance: {distance} meters, Duration: {duration} seconds")
    else:
        print("No precalculated route found for the given points.")