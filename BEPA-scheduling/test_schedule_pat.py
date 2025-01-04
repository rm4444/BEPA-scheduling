from scheduler import Scheduler
from models import Doctor, CalDay
from datetime import date


def setup_test_environment():
    pat = Doctor(
        name="PAT",
        days_off={date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 12),date(2024, 1, 13), date(2024, 1, 14), date(2024, 1, 15)},
        shift_prefs=[1, 1, 1, 5],
        min_shifts=14,
        max_shifts=17,
        previous_month_shifts=[(date(2023, 12, 28), 4),(date(2023, 12, 29), 4),(date(2023, 12, 30), 4),(date(2023, 12, 31), 4)]
    )
    calendar = [CalDay(date(2024, 1, day)) for day in range(1, 32)]
    return [pat], calendar

def run_test():
    # Set up the test environment
    doctors, calendar = setup_test_environment()

    # Print initialized calendar dates for debugging
    for cal_day in calendar[:5]:  # Print the first 5 days for inspection
        print(f"Initialized CalDay: {cal_day.date}")

    # Initialize scheduler
    scheduler = Scheduler(doctors, calendar)

    # Run PAT scheduling
    scheduler.schedule_pat()


if __name__ == "__main__":
    run_test()
