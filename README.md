# Police Incident Response Simulation

This Python project simulates police responses to incidents using an agent-based modeling approach. It combines incident simulation based on observed frequencies with travel time calculations to model how police officers respond to incidents in real time.

## Features

*   **Incident Simulation:**
    *   Generates incidents based on historical data, including their type, location, and time of occurrence.
    *   Uses Monte Carlo sampling to account for the random nature of incident occurrence.
    *   Incident types include immediate, prompt, scheduled, appointment, and no response required.
*   **Agent-Based Modeling:**
    *   Creates agents representing police officers and stations.
    *   Simulates officer behavior, including patrolling, responding to incidents, and traveling between locations.
    *   Tracks officer status (e.g., on duty, at the station, en route to incident).
*   **Travel Time Calculation:**
    *   Utilizes pre-processed OSRM data to estimate travel times between locations.
    *   Finds the nearest sampled points to the origin and destination to provide approximate travel times.
*   **Location Sampling:**
    *   Samples incident locations based on observed crime data and optional boundary constraints.
    *   Employs Kernel Density Estimation (KDE) to model the spatial distribution of crime types.
    *   Optionally uses rejection sampling to ensure incident locations are within a specified boundary.
*   **Logging:**
    *   Logs simulation events, incident details, and officer actions to track the simulation's progress.
    *   Provides valuable insights into the simulation's behavior for analysis and debugging.
*   **Data Structures:**
    *   Includes classes to represent incidents, officers, police stations, and the overall force control room (FCR).
    *   Utilizes dataclasses for convenient data storage and manipulation.
    *   Employs enums to represent different states and types in the simulation.


## Installation and Setup

1.  **Install Dependencies:**
    ```bash
    pip install pandas numpy scipy shapely geopandas
    ```
2.  **Acquire Data:**
    *   **Incident Frequencies:** Obtain a CSV file containing incident frequencies by weekday and hour (e.g., "incident_frequencies.csv").
    *   **Incident Locations:** Acquire a shapefile containing historical incident locations and crime types (e.g., "incident_locations.shp").
    *   **Border Shapefile (Optional):** If you want to restrict incident locations within a specific area, obtain a corresponding shapefile (e.g., "boundary.shp").
    *   **OSRM Data:** Prepare pre-processed OSRM data with sampled points and travel times (e.g., "sampled_points.shp" and "travel_times_distances.csv").

3.  **Place Data in Project Directory:**
    *   Place the data files in the project's main directory or specify their paths in the code where applicable.


## Usage

1.  **Configure Parameters:**
    *   Modify input file paths and other parameters in the Python scripts as needed.
2.  **Run Simulation:**
    ```bash
    python agent_sim_v2.py 
    ```
3.  **Analyze Results:**
    *   Review the generated log files to observe the simulation's behavior.
    *   Analyze the spatial distribution of incidents using the sampled locations.

## File Structure

*   `agent_sim_v2.py`: Core simulation logic, agent classes, and data structures.
*   `incident_estimator.py`:  Incident frequency estimation based on historical data.
*   `location_sampler.py`: Incident location sampling based on KDE and optional boundaries.
*   `travel_time_calculator.py`: Travel time estimation using OSRM data.

## Dependencies

*   pandas
*   numpy
*   scipy
*   shapely
*   geopandas



## Contributing

Contributions are welcome! Feel free to submit bug reports, feature requests, or pull requests.

## License

This project is licensed under the MIT License.

## Contact

For questions or feedback, please contact the author.
