import logging
import numpy
import os
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List
from shapely.geometry import Point, Polygon

class IncidentType(Enum):
    IMMEDIATE = 1
    PROMPT = 2
    SCHEDULED = 3
    APPOINTMENT = 4
    NO_RESPONSE = 5

class IncidentStatus(Enum):
    REPORTED = 1
    EN_ROUTE = 2
    ATTENDED = 3
    RESOLVED = 4

class ShiftType(Enum):
    EARLY = ("early", 7, 16)
    LATE = ("late", 15, 0)
    NIGHT = ("night", 22, 7)

    def __init__(self, name, start_hour, end_hour):
        self.name = name
        self.start_hour = start_hour
        self.end_hour = end_hour

@dataclass
class Shift:
    type: ShiftType

    @property
    def start_time(self) -> datetime.time:
        return datetime.time(self.type.start_hour)

    @property
    def end_time(self) -> datetime.time:
        return datetime.time(self.type.end_hour)
    

class OfficerStatus(Enum):
    URGENT_ASSISTANCE = ("00", "Urgent assistance")
    ON_DUTY = ("01", "On duty")
    ON_PATROL = ("02", "On patrol")
    AVAILABLE_AT_STATION = ("03", "Available at station")
    REFRESHMENTS = ("04", "Refreshments")
    ATTENDING_INCIDENT = ("05", "Attending incident (set by STORM)")
    ARRIVED_AT_SCENE = ("06", "Arrived at scene (set by STORM)")
    COMMITTED_BUT_DEPLOYABLE = ("07", "Committed but deployable (statement, paperwork etc)")
    COMMITTED_NOT_DEPLOYABLE = ("08", "Committed and NOT deployable (custody or interviewing)")
    PRISONER_ESCORT = ("09", "Prisoner escort")
    AT_COURT = ("10", "At court")
    OFF_DUTY = ("11", "Off duty")
    CONFIDENTIAL_MESSAGE = ("12", "Confidential message")
    RADIO_ON = ("99", "Radio on")

    def __init__(self, code, description):
        self.code = code
        self.description = description

    def __str__(self):
        return f"{self.code} - {self.description}"

    @classmethod
    def from_code(cls, code):
        for status in cls:
            if status.code == code:
                return status
        raise ValueError(f"Invalid status code: {code}")

@dataclass
class Incident:
    priority: IncidentType
    location: tuple  # (latitude, longitude)
    report_time: datetime.datetime  # In minutes since simulation start
    status: IncidentStatus = IncidentStatus.REPORTED
    response_time: datetime.timedelta = field(init=False, default=None)
    isr: str = field(init=False, default="PENDING")

@dataclass
class Officer:
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
        return [incident for incident in self.incidents if incident.status != IncidentStatus.ATTENDED]

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
        return f"HC-{date_str}-{incident.id:04d}"  # Format: YYYYMMDD/HHMM/0001

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
