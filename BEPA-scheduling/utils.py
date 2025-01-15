from models import *
#from scheduler import last3days, schedule1Shift, schedule2Shift, schedule3Shift, schedule4Shifts

import pandas as pd
import calendar
import xlrd
import openpyxl
import re
import numpy as np
from columnar import columnar
import math
import os

def print_calendar(calendar):
    """
    Print the calendar in a digestible 5-week grid format.
    Each day shows who is scheduled for each of the 4 shifts.
    """
    days_per_week = 7
    num_weeks = (len(calendar) + days_per_week - 1) // days_per_week

    print("\nSchedule for January 2024:")
    print("=" * 50)

    for week in range(num_weeks):
        # Extract days for the current week
        week_days = calendar[week * days_per_week : (week + 1) * days_per_week]

        # Print dates as headers
        print("  ".join(f"{day.date.strftime('%b %d')}" for day in week_days))

        # Print scheduled doctors for each shift
        for shift in range(1, 5):  # Shift 1 to Shift 4
            print("  ".join(day.scheduled_doctors.get(shift, "-----") for day in week_days))

        # Add a blank line between weeks
        print("\n")