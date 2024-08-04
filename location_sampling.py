import geopandas as gpd
from scipy.stats import gaussian_kde, iqr
from shapely.geometry import Point
import numpy as np
from typing import Tuple, Dict, Optional

class LocationSampler:
    def __init__(self, shapefile_path: str, border_path: Optional[str] = None) -> None:
        """
        Initializes the LocationSampler by loading incident data and an optional border shapefile.

        Args:
            shapefile_path (str): Path to the shapefile containing incident locations and crime types.
            border_path (Optional[str]): Optional path to the shapefile defining the boundary area of interest.
                                         If None, no rejection sampling will be performed.
        """

        # Load incident data from shapefile
        self.gdf = gpd.read_file(shapefile_path)
        self.mask_gdf = None
        if border_path:  # Only load mask_gdf if border_path is provided
            self.mask_gdf = gpd.read_file(border_path)  

        # Ensure shapefile has 'lon' and 'lat' columns (assuming geometry column is named 'geometry')
        self.gdf['lon'] = self.gdf.geometry.x  
        self.gdf['lat'] = self.gdf.geometry.y


        # Get unique crime types
        self.crime_types = self.gdf['crime_type'].unique()

        # Create Kernel Density Estimation (KDE) objects for each crime type
        self.kdes: Dict[str, gaussian_kde] = {}  # Dictionary to store KDEs for each crime type
        for crime_type in self.crime_types:
            # Filter data for specific crime type
            data = self.gdf[self.gdf['crime_type'] == crime_type][['lon', 'lat']].values

            # Calculate Silverman's bandwidth using standard deviation and interquartile range
            bw_lon = 0.9 * min(np.std(data[:, 0]), iqr(data[:, 0]) / 1.34) * len(data) ** (-1 / 5)
            bw_lat = 0.9 * min(np.std(data[:, 1]), iqr(data[:, 1]) / 1.34) * len(data) ** (-1 / 5)

            # Create KDE object and set bandwidths for each dimension
            kde = gaussian_kde(data.T)
            kde.covariance_factor = lambda: [bw_lon, bw_lat] 
            self.kdes[crime_type] = kde

    
    def sample_location(self, crime_type: str) -> Tuple[float, float]:
        """
        Samples a location, optionally within a specified border, based on the KDE for the given crime type.

        Args:
            crime_type (str): The type of crime for which to sample a location.

        Returns:
            Tuple[float, float]: A tuple containing the longitude and latitude of the sampled location.

        Raises:
            ValueError: If the given crime_type is not valid.
        """
        if crime_type not in self.crime_types:
            raise ValueError(f"Invalid incident type: {crime_type}")
        
        kde = self.kdes[crime_type]

        # Implement some rejection sampling here if generated points are outside of the border file
        while True:
            # Sample coordinates using the KDE
            sampled_coords = kde.resample(size=1).T[0]
            # Create a Point object representing the sampled location
            sampled_point = Point(sampled_coords[0], sampled_coords[1])
            # Check if border exists and if point is within the border
            if self.mask_gdf is None or self.mask_gdf.geometry.contains(sampled_point).any():  
                return sampled_coords[0], sampled_coords[1]
    
if __name__ == "__main__":
    location_sampler = LocationSampler("Geofiles/herts_crime_point_data.shp", "Geofiles/Borders/Hertfordshire Boundary.shp")
    lons = []
    lats = []
    for _ in range(10000):
        lon, lat = location_sampler.sample_location("Burglary")
        lons.append(lon), lats.append(lat)
        #print(f"Sampled location (lon, lat): ({lon:.4f}, {lat:.4f})")

    gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lons, lats), crs="EPSG:4326")
    gdf.to_file("scripts/burglary_geosample.shp")

    