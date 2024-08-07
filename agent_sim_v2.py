import logging
import numpy
import os
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List
from shapely.geometry import Point, Polygon

# Incident Type Enumeration: Defines categories for incident priority.
class IncidentType(Enum):
    """
    Represents the priority level of an incident.

    Members:
        IMMEDIATE (1): Highest priority, requires an immediate response.
        PROMPT (2): High priority, requires a prompt response.
        SCHEDULED (3): Pre-planned or scheduled incident.
        APPOINTMENT (4): Incident scheduled as an appointment.
        NO_RESPONSE (5): Incident that does not require a police response.
    """
    IMMEDIATE = 1
    PROMPT = 2
    SCHEDULED = 3
    APPOINTMENT = 4
    NO_RESPONSE = 5

# Incident Status Enumeration: Tracks the progress of an incident.
class IncidentStatus(Enum):
    """
    Represents the current status of an incident.

    Members:
        REPORTED (1): The incident has been reported.
        EN_ROUTE (2): Officers are en route to the incident.
        ATTENDED (3): Officers have arrived at the incident scene.
        RESOLVED (4): The incident has been resolved.
    """
    REPORTED = 1
    EN_ROUTE = 2
    ATTENDED = 3
    RESOLVED = 4

# Shift Type Enumeration: Defines different work shifts for officers.
class ShiftType(Enum):
    """
    Represents the type of shift an officer is working.

    Members:
        EARLY ("early", 7, 16): Early shift (7 AM to 4 PM).
        LATE ("late", 15, 0): Late shift (3 PM to 12 AM).
        NIGHT ("night", 22, 7): Night shift (10 PM to 7 AM).
    """
    EARLY = ("early", 7, 16)
    LATE = ("late", 15, 0)
    NIGHT = ("night", 22, 7)

    # Constructor for ShiftType to store shift name, start, and end hours
    def __init__(self, name, start_hour, end_hour):
        self.name = name
        self.start_hour = start_hour
        self.end_hour = end_hour

@dataclass
class Shift:
    """
    Represents a specific work shift for a police officer.

    Attributes:
        type (ShiftType): The type of shift (e.g., EARLY, LATE, NIGHT).

    Properties:
        start_time (datetime.time): The start time of the shift.
        end_time (datetime.time): The end time of the shift.
    """
    type: ShiftType

    @property
    def start_time(self) -> datetime.time:
        return datetime.time(self.type.start_hour)

    @property
    def end_time(self) -> datetime.time:
        return datetime.time(self.type.end_hour)
    

class OfficerStatus(Enum):
    """
    Represents the detailed status of a police officer.

    Members:
        URGENT_ASSISTANCE ("00", "Urgent assistance"): 
            Officer requires immediate assistance.
        ON_DUTY ("01", "On duty"): 
            Officer is on duty and available for assignment.
        ON_PATROL ("02", "On patrol"): 
            Officer is actively patrolling their assigned area.
        AVAILABLE_AT_STATION ("03", "Available at station"): 
            Officer is at the station and available for deployment.
        REFRESHMENTS ("04", "Refreshments"): 
            Officer is taking a break for refreshments.
        ATTENDING_INCIDENT ("05", "Attending incident"): 
            Officer is en route to or at the scene of an incident.
        ARRIVED_AT_SCENE ("06", "Arrived at scene"): 
            Officer has arrived at the scene of an incident.
        COMMITTED_BUT_DEPLOYABLE ("07", "Committed but deployable (statement, paperwork etc)"): 
            Officer is engaged in an activity but can be reassigned if necessary (e.g., taking a statement).
        COMMITTED_NOT_DEPLOYABLE ("08", "Committed and NOT deployable (custody or interviewing)"): 
            Officer is engaged in an activity that prevents them from being reassigned (e.g., in custody).
        PRISONER_ESCORT ("09", "Prisoner escort"): 
            Officer is escorting a prisoner.
        AT_COURT ("10", "At court"): 
            Officer is attending court.
        OFF_DUTY ("11", "Off duty"): 
            Officer is off duty and unavailable for assignment.
        CONFIDENTIAL_MESSAGE ("12", "Confidential message"):
            Officer is receiving a confidential message.
        RADIO_ON ("99", "Radio on"): 
            Officer's radio is turned on (general status).

    Methods:
        __init__(self, code, description):
            Initializes an OfficerStatus member with a code and description.
        __str__(self) -> str:
            Returns a string representation of the officer status in the format "code - description" (e.g., "01 - On duty").
        from_code(cls, code: str) -> OfficerStatus:
            Class method that returns the OfficerStatus member associated with the given code. Raises a ValueError if the code is invalid.
    """
    URGENT_ASSISTANCE = ("00", "Urgent assistance")
    ON_DUTY = ("01", "On duty")
    ON_PATROL = ("02", "On patrol")
    AVAILABLE_AT_STATION = ("03", "Available at station")
    REFRESHMENTS = ("04", "Refreshments")
    ATTENDING_INCIDENT = ("05", "Attending incident")
    ARRIVED_AT_SCENE = ("06", "Arrived at scene")
    COMMITTED_BUT_DEPLOYABLE = ("07", "Committed but deployable (statement, paperwork etc)")
    COMMITTED_NOT_DEPLOYABLE = ("08", "Committed and NOT deployable (custody or interviewing)")
    PRISONER_ESCORT = ("09", "Prisoner escort")
    AT_COURT = ("10", "At court")
    OFF_DUTY = ("11", "Off duty")
    CONFIDENTIAL_MESSAGE = ("12", "Confidential message")
    RADIO_ON = ("99", "Radio on")

    def __init__(self, code, description):
        """
        Initializes an OfficerStatus member.

        Args:
            code (str): The two-digit code representing the status.
            description (str): A human-readable description of the status.
        """
        self.code = code
        self.description = description

    def __str__(self):
        """
        Returns a string representation of the officer status.

        Returns:
            str: A string in the format "code - description" (e.g., "01 - On duty").
        """
        return f"{self.code} - {self.description}"

    @classmethod
    def from_code(cls, code):
        """
        Retrieves the OfficerStatus member associated with the given code.

        Args:
            code (str): The two-digit code representing the status.

        Returns:
            OfficerStatus: The corresponding OfficerStatus member.

        Raises:
            ValueError: If the provided code is invalid.
        """
        for status in cls:
            if status.code == code:
                return status
        raise ValueError(f"Invalid status code: {code}")

@dataclass
class Incident:
    """
    Represents an incident that requires police attention.

    Attributes:
        priority (IncidentType): The priority level of the incident.
        location (tuple): The geographic location of the incident (latitude, longitude).
        report_time (datetime.datetime): The time the incident was reported.
        status (IncidentStatus): The current status of the incident (default: REPORTED).
        station (PoliceStation): The police station responsible for the incident (default: None).
        assigned_officer (Officer): The officer assigned to the incident (default: None). 
        travel_time (float): The estimated travel time in seconds for the officer to reach the incident (default: None).
        resolution_time (float): The estimated time in seconds to resolve the incident after arrival (default: None).
        isr (str): The Incident Serial Reference (ISR) (default: "PENDING").
    """
    priority: IncidentType
    location: tuple
    report_time: datetime.datetime
    status: IncidentStatus = IncidentStatus.REPORTED
    station: PoliceStation = field(default=None)   
    assigned_officer: Officer = field(default=None)  
    travel_time: float = field(default=None)
    resolution_time: float = field(default=None)
    isr: str = field(init=False, default="PENDING")

@dataclass
class Officer:
    """
    Represents a police officer in the simulation.

    Attributes:
        id (int): Unique identifier for the officer.
        station (PoliceStation): The station the officer is assigned to.
        status (str): The current status of the officer (default: "available").
        current_location (tuple): The officer's current location (latitude, longitude).
        assigned_incident (Incident): The incident the officer is currently responding to (default: None).
        travel_route (list): The list of locations the officer will visit to reach their destination (default: empty list).
        shift (Shift): The officer's assigned work shift.
        end_time (datetime.datetime): The calculated end time of the officer's shift.
    
    Methods:
        __post_init__(self, simulation_time: datetime.datetime): 
            Calculates the officer's actual shift end time based on the simulation start time and shift start time.
        is_on_duty(self, simulation_time: datetime.datetime) -> bool:
            Checks if the officer is currently on duty based on the simulation time and their shift.
    """
    id: int
    station: object  # Reference to the PoliceStation object
    status: str = "available"
    current_location: tuple = field(init=False)  # Set initially to station location
    assigned_incident: Incident = field(init=False, default=None)
    travel_route: list = field(init=False, default_factory=list)
    shift: Shift
    end_time: datetime.datetime = field(init=False)

    def __post_init__(self, simulation_time: datetime.datetime):
        # Calculate the actual end time based on shift start time and simulation time
        if self.shift.start_time < simulation_time.time():
            self.end_time = datetime.datetime.combine(simulation_time.date(), self.shift.end_time)
        else:
            self.end_time = datetime.datetime.combine(simulation_time.date() + datetime.timedelta(days=1), self.shift.end_time)

    def is_on_duty(self, simulation_time: datetime.datetime) -> bool:
        return self.shift.start_time <= simulation_time.time() <= self.end_time.time()



class PoliceStation:
    """
    Represents a police station with a location, officers, and a response area.

    Attributes:
        location (Point): Geographic location of the station (latitude, longitude).
        officers (list): List of officers assigned to the station.
        name (str): Name of the police station.
        id (int): Unique identifier for the station.
        response_area (Polygon): Geographic area that the station is responsible for.

    Methods:
        add_officer(self, officer: Officer):
            Adds an officer to the station.
        get_officers(self) -> List[Officer]:
            Returns a list of all officers assigned to the station.
    """
    def __init__(self, location: tuple, name: str, id: int, response_area: Polygon):
        self.location = Point(location)
        self.officers = []
        self.name = name
        self.id = id
        self.response_area = response_area  

    def add_officer(self, officer: Officer):
        self.officers.append(officer)
        officer.station = self

    # Remove get_available_officers, assign_officer_to_incident, and is_incident_in_response_area

    def get_officers(self) -> List[Officer]:
        """Returns all officers associated with the station."""
        return self.officers


@dataclass
class FCR:
    """
    Force Control Room: Central hub for managing incidents and police resources.

    Attributes:
        stations (List[PoliceStation]): List of police stations under FCR control.
        incidents (List[Incident]): List of active incidents.

    Methods:
        add_incident(self, incident: Incident):
            Adds a new incident to the FCR and attempts to assign an officer.
        
        find_responsible_station(self, location: Point) -> PoliceStation:
            Returns the police station responsible for handling an incident at the given location. If no station is found, logs an error.

        get_available_officers(self, station: PoliceStation) -> List[Officer]:
            Returns a list of available officers from the specified station who are currently on duty.

        find_closest_station(self, location: Point, num_stations=2) -> List[PoliceStation]:
            Returns a list of the closest police stations (up to num_stations) to the given location, sorted by distance.

        assign_incident(self, incident: Incident):
            Attempts to assign the given incident to an available officer.

        get_incident_by_id(self, incident_id: int) -> Incident:
            Returns the incident object with the specified ID, or None if not found.

        get_unattended_incidents(self) -> List[Incident]:
            Returns a list of all incidents that have not yet been attended to.

        sort_by_priority_and_time(self, incidents: List[Incident]) -> List[Incident]:
            Sorts a list of incidents by priority (descending) and then by report time (ascending).

        get_highest_priority_incident(self, incidents: List[Incident], current_time: datetime.datetime) -> Incident:
            Returns the highest priority unattended incident from the list, considering the time since the incident was reported.

        gen_isr(self, incident: Incident) -> str:
            Generates a unique Incident Serial Reference (ISR) for the incident.

        determine_station_priority(self, incident: Incident) -> List[PoliceStation]:
            Determines the order in which to try assigning the incident to stations based on distance, available officers, and workload.

        assign_officer_to_incident(self, incident: Incident, station: PoliceStation) -> bool:
            Assigns an available officer from the given station to the incident, returns True if successful, False otherwise.

        assign_incident(self, incident: Incident):
            Attempts to assign the incident to the most appropriate station based on a priority order.
    """

    stations: List[PoliceStation]
    incidents: List[Incident] = field(default_factory=list)

    def add_incident(self, incident: Incident):
        self.incidents.append(incident)
        self.assign_incident(incident)  # Immediately try to assign

    def find_responsible_station(self, location: Point) -> PoliceStation:
        for station in self.stations:
            if station.response_area.contains(location):
                return station
        logging.error(f"No responsible station found for incident at {location}")
        return None  # Or handle this case differently (e.g., assign to a default station)

    def get_available_officers(self, station: PoliceStation) -> List[Officer]:
        return [
            officer
            for officer in station.get_officers()
            if officer.assigned_incident is None and officer.is_on_duty()
        ]

    def find_closest_station(self, location: Point, num_stations=2) -> List[PoliceStation]:
        sorted_stations = sorted(self.stations, key=lambda s: s.location.distance(location))
        return sorted_stations[:num_stations]

    def assign_incident(self, incident: Incident):
        """
        Main incident assignment logic. TO DO!
        """
        responsible_station = self.find_responsible_station(incident.location)

        if responsible_station:
            if responsible_station.assign_officer_to_incident(incident):
                return  # Assignment successful at primary station

            # If no officers available at the responsible station, try nearby stations
            nearby_stations = self.find_closest_station(incident.location, num_stations=2)
            for station in nearby_stations:
                if station != responsible_station and station.assign_officer_to_incident(incident):
                    return  # Assignment successful at a nearby station
        
        # If still no assignment, log an error or take other action
        logging.error(f"No available officers for incident {incident.id} in any nearby station.") 

    def get_incident_by_id(self, incident_id: int) -> Incident:
        for incident in self.incidents:
            if incident.id == incident_id:
                return incident
        return None
    
    def get_unattended_incidents(self) -> List[Incident]:
        """
        Returns a list of reported incidents (excluding en-route and attended).

        Returns:
            List[Incident]: A list of reported incidents.
        """
        return [incident for incident in self.incidents if incident.status == IncidentStatus.REPORTED]

    def get_all_unresolved_incidents(self) -> List[Incident]:
        """
        Returns a list of all unresolved incidents (reported and en-route).

        Returns:
            List[Incident]: A list of all unresolved incidents.
        """
        return [incident for incident in self.incidents if incident.status != IncidentStatus.ATTENDED and incident.status != IncidentStatus.RESOLVED]

    def sort_by_priority_and_time(self, incidents: List[Incident]) -> List[Incident]:
        """Sorts incidents by priority (descending) and then by time of occurrence (ascending)."""
        return sorted(incidents, key=lambda incident: (-incident.priority, incident.report_time))

    def get_highest_priority_incident(self, incidents: List[Incident], current_time: datetime.datetime) -> Incident:
        """Returns the highest priority unattended incident, considering time since creation."""
        sorted_incidents = self.sort_by_priority_and_time(incidents)
        for incident in sorted_incidents:
            if incident.status != IncidentStatus.ATTENDED:
                return incident
        return None

    def gen_isr(self, incident: Incident) -> str:
        """Generates a unique ISR (Incident Serial Reference) for the incident."""
        # Assuming you have a function to format dates and times as strings:
        date_str = incident.report_time.strftime("%Y%m%d")  
        time_str = incident.report_time.strftime("%H%M")
        incident_logger.info(f"Incident created ISR HC-{date_str}-{incident.id:04d} at {date_str}-{time_str}")
        return f"Inc-{date_str}-{incident.id:04d}"  # Format: YYYYMMDD/HHMM/0001
    
    def determine_station_priority(self, incident: Incident) -> List[PoliceStation]:
        """Determine the order in which to try assigning the incident to stations."""
        def priority_key(station: PoliceStation):
            distance = station.location.distance(incident.location)
            available_officers = len(self.get_available_officers(station))
            workload = len([inc for inc in self.incidents if inc.station == station])  # This is a simplification, adjust as needed
            return distance, -available_officers, workload  # Prioritize: closer, more available, less workload
        
        candidate_stations = [s for s in self.stations if s.response_area.contains(incident.location)]
        return sorted(candidate_stations, key=priority_key)
    
    def assign_officer_to_incident(self, incident: Incident, station: PoliceStation) -> bool:
        """Tries to assign an available officer from the given station to the incident."""
        available_officers = self.get_available_officers(station)
        if not available_officers:
            return False
       
        closest_officer = min(available_officers, key=lambda officer: officer.current_location.distance(incident.location))

        closest_officer.assigned_incident = incident
        incident.status = IncidentStatus.EN_ROUTE
        incident.station = station
        return True

    def assign_incident(self, incident: Incident):
        station_priority = self.determine_station_priority(incident)
        for station in station_priority:
            if self.assign_officer_to_incident(incident, station):
                return  # Assignment successful


if __name__ == "__main__":

    # Create a logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure logging
    log_filename = os.path.join(log_dir, f"simulation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")  # Unique log file name

    logging.basicConfig(
        filename=log_filename,  # Log to a file
        level=logging.INFO,     # Set minimum level to INFO (or DEBUG for more detail)
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Customize the format
    )

    # Get the root logger and add a handler for console output
    console_handler = logging.StreamHandler()  # Send logs to the console as well
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)

    # Create loggers for different parts of your application
    fcr_logger = logging.getLogger("FCR")
    station_logger = logging.getLogger("PoliceStation")
    incident_logger = logging.getLogger("Incident")

    # Arbitrary start time 2024-01-01 09:00:00
    sim_start_time = datetime.datetime(2024,1,1,9,0,0)

    timestep = datetime.timedelta(minutes=5)

    # Set up police stations

# First stab at simulation logic:

def main_simulation_loop(fcr: FCR, total_time: datetime.timedelta, timestep: datetime.timedelta, start_time: datetime.datetime):
    """
    Runs the main simulation loop for the specified duration.

    Args:
        fcr (FCR): The Force Control Room object managing incidents and officers.
        total_time (datetime.timedelta): The total duration of the simulation.
        timestep (datetime.timedelta): The time interval between each simulation step.
        start_time (datetime.datetime): The starting datetime of the simulation.
    """

    current_time = start_time
    end_time = start_time + total_time
    incidents_attended = []
    incident_counter = 1

    while current_time < end_time:
        # 1. Generate new incidents (You'll implement this in another file)
        # new_incidents = generate_incidents(current_time, timestep)  

        # 2. Add new incidents to the backlog and sort
        # for incident in new_incidents:
        #     incident.id = incident_counter
        #     fcr.add_incident(incident)
        #     incident_counter += 1

        # 3. Assign reported incidents from the backlog
        while fcr.incident_backlog and any(officer.status == OfficerStatus.AVAILABLE_AT_STATION.value for station in fcr.stations for officer in station.officers):
            incident = fcr.incident_backlog.pop(0)  # Get the highest priority incident

            # Find the responsible station for the incident
            responsible_station = fcr.find_responsible_station(Point(incident.location))

            if responsible_station:
                available_officers = fcr.get_available_officers(responsible_station) 
                if available_officers:
                    assigned_officer = available_officers[0]
                    assigned_officer.status = OfficerStatus.ATTENDING_INCIDENT.value
                    assigned_officer.assigned_incident = incident
                    incident.status = IncidentStatus.EN_ROUTE
                    incidents_attended.append(incident)
                    
                    # 4. Calculate and store travel time (You'll implement this in travel_time_calc.py)
                    # travel_time = calculate_travel_time(assigned_officer.current_location, incident.location)
                    # incident.travel_time = travel_time[1]  # Assuming the second element is the duration in seconds
                else:
                    # No available officers at the responsible station, so don't remove from backlog yet
                    fcr.incident_backlog.insert(0, incident)  # Re-insert at the beginning
                    break  # Exit the inner loop and try the next incident


        # 5. Update incidents being attended and resolve completed incidents
        for incident in incidents_attended:
            # incident.travel_time -= timestep.total_seconds()
            if incident.status == IncidentStatus.EN_ROUTE and incident.travel_time <= 0:
                incident.status = IncidentStatus.ATTENDED
                incident.travel_time = None  # Reset travel time
                # incident.resolution_time = numpy.random.uniform(15 * 60, 30 * 60)  # 15-30 minutes in seconds

            if incident.status == IncidentStatus.ATTENDED:
                incident.resolution_time -= timestep.total_seconds()
                if incident.resolution_time <= 0:
                    incident.status = IncidentStatus.RESOLVED
                    assigned_officer = next(officer for station in fcr.stations for officer in station.officers if officer.assigned_incident == incident)
                    assigned_officer.status = OfficerStatus.AVAILABLE_AT_STATION.value
                    assigned_officer.assigned_incident = None
                    incidents_attended.remove(incident)
                    
        
        # Logging
        logging.info(f"Timestep: {current_time}, Reported: {len(fcr.incident_backlog)}, "
                     f"En Route/Attending: {len(incidents_attended)}, Resolved: {len([inc for inc in fcr.incidents if inc.status == IncidentStatus.RESOLVED])}")

        # Move to the next time step
        current_time += timestep
