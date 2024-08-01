import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import datetime

def estimate_incidents(df, weekday, start_time, duration, monte_carlo=False):
  # Extract hour and minute from start_time
  start_hour = start_time.hour
  start_minute = start_time.minute

  # Extract duration in minutes from timedelta object
  duration_minutes = duration.seconds // 60

  # Calculate end_time, handling wrap-arounds for hours and minutes
  end_hour = (start_hour + (start_minute + duration_minutes) // 60) % 24
  end_minute = (start_minute + duration_minutes) % 60
  end_time = (end_hour, end_minute)

  # Determine start and end days, handling wrap-arounds for days and weeks
  weekdays = list(df.columns)[1:]
  start_day_index = weekdays.index(weekday)
  end_day_index = (start_day_index + (end_hour < start_hour)) % 7
  end_day = weekdays[end_day_index]

  # Get relevant rows from the DataFrame, handling wrap-arounds
  relevant_rows = df[((df['Hr'] >= start_hour) | (df['Hr'] <= end_hour)) & (df['Hr'] != 24)].copy()

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
      total_incidents += row[weekday] * (60 - start_minute) / 60
    elif row['Hr'] == end_hour:
      total_incidents += row[end_day] * end_minute / 60
    else:
      total_incidents += row[weekday]

  # Adjust for the duration if it spans multiple hours
  total_incidents *= duration_minutes / 60

  if monte_carlo:
    return np.random.poisson(total_incidents)
  else:
    return total_incidents

# Read the CSV file into a DataFrame
df = pd.read_csv('Incident Generation.csv')

# Test cases
test_cases = [
  ("Monday", datetime.datetime(year=2023, month=1, day=1, hour=9, minute=30), datetime.timedelta(minutes=120), False),  # Expected value
  ("Monday", datetime.datetime(year=2023, month=1, day=1, hour=9, minute=30), datetime.timedelta(minutes=120), True),   # Monte Carlo sample
  ("Friday", datetime.datetime(year=2023, month=1, day=5, hour=23, minute=45), datetime.timedelta(minutes=90), False),
  ("Friday", datetime.datetime(year=2023, month=1, day=5, hour=23, minute=45), datetime.timedelta(minutes=90), True),
  ("Saturday", datetime.datetime(year=2023, month=1, day=6, hour=22, minute=0), datetime.timedelta(minutes=180), False),
  ("Saturday", datetime.datetime(year=2023, month=1, day=6, hour=22, minute=0), datetime.timedelta(minutes=180), True)
]

for weekday, start_time, duration, monte_carlo in test_cases:
  estimated_incidents = estimate_incidents(df, weekday, start_time, duration, monte_carlo)
  if monte_carlo:
    print(f"Monte Carlo sample of incidents for {weekday}, starting at {start_time}, duration {duration}: {estimated_incidents}")
  else:
    print(f"Estimated incidents for {weekday}, starting at {start_time}, duration {duration}: {estimated_incidents:.2f}")