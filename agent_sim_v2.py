import logging
import numpy
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List

class IncidentType(Enum):
    IMMEDIATE = 1
    PROMPT = 2
    SCHEDULED = 3
    APPOINTMENT = 4
    NO_RESPONSE = 0

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

    def gen_isr(self, uid) -> str:
        """The input "uid" is a unique identifier which is generally an integer to 4 significant
        figures generated serially from the first incident of the day having a uid of 1 onwards.
        While this would pose problems if more than 9999 incidents occur in a day, the maximum
        value experienced in this county is <2500."""
        return "{}-{}-{:0>4}".format("HC", self.datetime.date, uid)

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

@dataclass
class IncidentManager:
    incidents: List[Incident] = field(default_factory=list)
    next_incident_id: int = 1

    def add_incident(self, incident: Incident):
        incident.id = self.next_incident_id
        self.incidents.append(incident)
        self.next_incident_id += 1

    def get_unattended_incidents(self) -> List[Incident]:
        return [incident for incident in self.incidents if incident.status != IncidentStatus.ATTENDED]

    def sort_by_priority_and_time(self, incidents: List[Incident]) -> List[Incident]:
        """Sorts incidents by priority (descending) and then by time of occurrence (ascending)."""
        return sorted(incidents, key=lambda incident: (-incident.priority, incident.time_of_occurrence))

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
        date_str = incident.time_of_occurrence.strftime("%Y%m%d")  
        time_str = incident.time_of_occurrence.strftime("%H%M")
        return f"{date_str}/{time_str}/{incident.id:04d}"  # Format: YYYYMMDD/HHMM/0001

    def get_incident_by_id(self, incident_id: int) -> Incident:
        """Retrieves an incident by its ID."""
        for incident in self.incidents:
            if incident.id == incident_id:
                return incident
        return None
