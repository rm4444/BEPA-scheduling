from models import *
from scheduler import Scheduler
from utils import print_calendar
from datetime import date, timedelta

import numpy as np
from columnar import columnar

def setup_test_environment():
    doctors = [
        Doctor(
            name="Doctor A",
            days_off={date(2024, 1, 10), date(2024, 1, 11)},
            shift_prefs=[2, 3, 4, 3],  # Strong preference for 4 shifts
            min_shifts=10,
            max_shifts=15,
        ),
        Doctor(
            name="Doctor B",
            days_off={date(2024, 1, 12), date(2024, 1, 13)},
            shift_prefs=[3, 2, 1, 3],  # Prefers 4 shifts the same as than Doctor A
            min_shifts=10,
            max_shifts=16,
        ),
        Doctor(
            name="Doctor C",
            days_off={date(2024, 1, 9), date(2024, 1, 14)},
            shift_prefs=[1, 2, 3, 1],  # Lowest preference for 4 shifts
            min_shifts=12,
            max_shifts=20,
        ),
    ]

    # PAT's schedule is already filled for test
    pat = Doctor(
        name="PAT",
        days_off={date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 15)},
        shift_prefs=[1, 1, 1, 5],
        min_shifts=14,
        max_shifts=17,
        previous_month_shifts=[(date(2023, 12, 29), 4), (date(2023, 12, 30), 4)],
    )

    calendar = [CalDay(date(2024, 1, day)) for day in range(1, 32)]

    # Schedule PAT shifts to create gaps
    scheduler = Scheduler([pat] + doctors, calendar)
    scheduler.schedule_pat()
    
    return doctors, calendar, scheduler

def test_schedule_remaining_shift4():
    doctors, calendar, scheduler = setup_test_environment()

    # Run scheduling for remaining 4 shifts
    scheduler.schedule_remaining_shift4()

    # Print the results
    print("\nSchedule Results:")
    for cal_day in calendar:
        if cal_day.shift_assignments.get(4):
            assigned_doc = cal_day.shift_assignments[4].name
            print(f"Day {cal_day.date}: Shift 4 assigned to {assigned_doc}")
        else:
            print(f"Day {cal_day.date}: Shift 4 is unfilled.")

if __name__ == "__main__":
    test_schedule_remaining_shift4()
