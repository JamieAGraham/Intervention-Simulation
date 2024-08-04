import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import datetime
from typing import Union

class IncidentEstimator:
    def __init__(self, csv_file_path: str) -> None:
        """Initialize the class by loading the CSV data."""
        self.df = pd.read_csv(csv_file_path)

    def estimate_incidents(self, weekday: str, start_time: datetime.datetime, 
                            duration: datetime.timedelta, monte_carlo: bool = False) -> Union[float, int]:

        """Estimate the number of incidents for the given parameters.

        Args:
            weekday (str): The day of the week (e.g., "Monday").
            start_time (datetime): The datetime object representing the start time.
            duration (timedelta): The timedelta object representing the duration.
            monte_carlo (bool): Whether to use Monte Carlo sampling (default: False).

        Returns:
            float or int: The estimated or sampled number of incidents.
        """
        start_hour = start_time.hour
        start_minute = start_time.minute

        duration_minutes = duration.seconds // 60

        end_hour = (start_hour + (start_minute + duration_minutes) // 60) % 24
        end_minute = (start_minute + duration_minutes) % 60
        end_time = (end_hour, end_minute)

        weekdays = list(self.df.columns)[1:]
        start_day_index = weekdays.index(weekday)
        end_day_index = (start_day_index + (end_hour < start_hour)) % 7
        end_day = weekdays[end_day_index]

        # Select correct rows based on start and end hour, accounting for wrap-around
        if start_hour < end_hour:  # Duration doesn't cross midnight
            relevant_rows = self.df[(self.df['Hr'] >= start_hour) & (self.df['Hr'] < end_hour)].copy()
        else:  # Duration crosses midnight
            relevant_rows = self.df[(self.df['Hr'] >= start_hour) | (self.df['Hr'] < end_hour)].copy()
        

        # If no relevant rows are found, return 0
        if relevant_rows.empty:
            return 0
        

        # Interpolate incident rates for partial hours
        for day in [weekday, end_day]:
            if (day == weekday and start_minute != 0) or (day == end_day and end_minute != 0):
                x = relevant_rows['Hr']
                y = relevant_rows[day]
                f = interp1d(x, y, kind='linear', fill_value='extrapolate')
                if day == weekday:
                    relevant_rows.loc[relevant_rows['Hr'] == start_hour, day] = f(start_hour + start_minute / 60)
                else:
                    relevant_rows.loc[relevant_rows['Hr'] == end_hour, day] = f(end_hour + end_minute / 60)

        # Calculate total incidents, accounting for duration and wrap-arounds
        total_incidents = 0
        for _, row in relevant_rows.iterrows():
            if row['Hr'] == start_hour:
                total_incidents += row[weekday] * (60 - start_minute) / 60  # Correctly scale only the start hour
            elif row['Hr'] == end_hour and end_hour != start_hour:  # Avoid double counting end_hour if it's the same as start_hour
                total_incidents += row[end_day] * end_minute / 60  # Correctly scale only the end hour
            elif start_hour < end_hour and row['Hr'] > start_hour and row['Hr'] < end_hour:  # Full hours within the duration
                total_incidents += row[weekday]  # Add full hour without scaling
            elif start_hour > end_hour and (row['Hr'] > start_hour or row['Hr'] < end_hour):  # Full hours across midnight
                total_incidents += row[weekday]  # Add full hour without scaling

        if monte_carlo:
            return np.random.poisson(total_incidents)
        else:
            return total_incidents

if __name__ == "__main__":
  # Read the CSV file into a DataFrame, filename here example version
  df = pd.read_csv('Incident Generation Example.csv')

  # Test cases


    # Example usage in another script:
  estimator = IncidentEstimator('Incident Generation Example.csv')  # Replace with actual file path

  test_cases = [
    ("Monday", datetime.datetime(year=2023, month=1, day=1, hour=9, minute=30), datetime.timedelta(minutes=120), False),  # Expected value
    ("Monday", datetime.datetime(year=2023, month=1, day=1, hour=9, minute=30), datetime.timedelta(minutes=120), True),   # Monte Carlo sample
    ("Friday", datetime.datetime(year=2023, month=1, day=5, hour=23, minute=45), datetime.timedelta(minutes=90), False),
    ("Friday", datetime.datetime(year=2023, month=1, day=5, hour=23, minute=45), datetime.timedelta(minutes=90), True),
    ("Saturday", datetime.datetime(year=2023, month=1, day=6, hour=22, minute=0), datetime.timedelta(minutes=180), False),
    ("Saturday", datetime.datetime(year=2023, month=1, day=6, hour=22, minute=0), datetime.timedelta(minutes=180), True)
  ]

  for weekday, start_time, duration, monte_carlo in test_cases:
      estimated_incidents = estimator.estimate_incidents(weekday, start_time, duration, monte_carlo)
      if monte_carlo:
          print(f"Monte Carlo sample of incidents for {weekday}, starting at {start_time}, duration {duration}: {estimated_incidents}")
      else:
          print(f"Estimated incidents for {weekday}, starting at {start_time}, duration {duration}: {estimated_incidents:.2f}")