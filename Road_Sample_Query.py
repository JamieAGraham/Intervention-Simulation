import geopandas as gpd
import requests
import pandas as pd
import time
from tqdm import tqdm  

# Load sampled points
sampled_points_gdf = gpd.read_file('sampled_points_proportional.shp')
sampled_points_gdf = sampled_points_gdf.to_crs("EPSG:4326")

# Base URL for your OSRM API
base_url = 'http://127.0.0.1:5000/route/v1/driving/'  

# Function to query OSRM
def query_osrm(coords):
    url = base_url + ';'.join([f"{coord[0]},{coord[1]}" for coord in coords]) + '?overview=false' 

    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        return data['routes'][0]['distance'], data['routes'][0]['duration']
    else:
        return None, None

# Initialize a DataFrame to store results
results_df = pd.DataFrame(columns=['point1_index', 'point2_index', 'distance_metres', 'duration_seconds'])

total_pairs = len(sampled_points_gdf) * (len(sampled_points_gdf) - 1) // 2

def save_intermediate_results(results_df, i):
    filename = f'Travel Time CSVs\\travel_times_distances.csv'
    results_df.to_csv(filename, index=False)
    print(f"Saved intermediate results for i={i} to {filename}")

start_time = time.time()

# Iterate through pairs of points
with tqdm(total=total_pairs, desc="Calculating travel times and distances") as pbar:
    for i in range(len(sampled_points_gdf)):
        for j in range(i + 1, len(sampled_points_gdf)):  # Avoid duplicate queries
            point1 = sampled_points_gdf.iloc[i]['geometry'].coords[0]
            point2 = sampled_points_gdf.iloc[j]['geometry'].coords[0]
            distance, duration = query_osrm([point1, point2])

            # Add results to DataFrame (converting indices to integers)
            if distance is not None:  
                results_df.loc[len(results_df)] = [int(i), int(j), distance, duration]

            
                
        save_intermediate_results(results_df, i)

        # Update progress bar and display time estimates
        pbar.update(len(sampled_points_gdf) - i - 1)  # Update for remaining pairs with current i
        elapsed_time = time.time() - start_time
        estimated_time_remaining = (elapsed_time / pbar.n) * (pbar.total - pbar.n)
        pbar.set_postfix({
            "Elapsed": f"{elapsed_time:.2f}s",
            "ETA": f"{estimated_time_remaining:.2f}s"
        })


results_df['point1_index'] = results_df['point1_index'].astype(int)
results_df['point2_index'] = results_df['point2_index'].astype(int)

# Save the results to a file
results_df.to_csv('travel_times_distances.csv', index=False)