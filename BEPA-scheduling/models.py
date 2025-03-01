from datetime import *

class Doctor:
    def __init__(self, name, days_off, shift_prefs, min_shifts, max_shifts, flip_shifts, doc_type):
        """
        Initialize a doctor with their attributes.

        Args:
            name (str): Doctor's name.
            days_off (list): Days the doctor cannot work.
            shift_prefs (list): Preferred shifts (1, 2, 3, 4).
            min_shifts (int): Minimum shifts the doctor wants to work.
            max_shifts (int): Maximum shifts the doctor can work.
            flip_shifts (boolean): If True, then invert days requested off
            doc_type (string): E.g., full time, part time, locums
            previous_month_shifts (list): Shifts worked in the last 3 days of the previous month.
        """
        self.name = name
        self.days_off = {day if isinstance(day, date) else date(2024, 1, day) for day in days_off}
        self.shift_prefs = shift_prefs
        self.min_shifts = min_shifts
        self.max_shifts = max_shifts
        self.flip_shifts = flip_shifts
        self.doc_type = doc_type
        self.total_shifts = 0
        self.night_shifts = 0
        self.weekend_shifts = 0
        self.consecutive_shifts = 0
        self.last_shift_date = datetime.min.date()
        self.previous_month_shifts = []

        # Initialize consecutive shifts based on the last month
        self.initialize_consecutive_shifts()

    def initialize_consecutive_shifts(self):
        """
        Calculate the initial consecutive shifts based on the previous month's data.
        """
        self.consecutive_shifts = sum(1 for date, shift_type in self.previous_month_shifts if shift_type)

    def can_work(self, date, shift_type, is_weekend=False):
        """
        Check if the doctor can work a specific shift on a given date.

        Args:
            date (int): The current date.
            shift_type (int): The shift type (1, 2, 3, or 4).
            is_weekend (bool): Whether the shift is on a weekend.

        Returns:
            bool: True if the doctor can work, False otherwise.
        """
        # Standard availability checks
        if date in self.days_off:
            return False
        if self.total_shifts >= self.max_shifts:
            return False
        if self.consecutive_shifts >= 4:  # Example: 4 consecutive shifts max
            return False
        return True

    def assign_shift(self, cal_day, shift_type):
        """
        Assigns a shift to the doctor and updates shift tracking.

        Args:
            cal_day (CalendarDay): The day the shift is assigned.
            shift_type (str): The type of shift being assigned.
        """

        # Assign shift and update counts
        self.total_shifts += 1
        if shift_type == "s4":
            self.night_shifts += 1
        if cal_day.weekend:
            self.weekend_shifts += 1
        self.last_shift_date = cal_day


class CalDay:
    def __init__(self, date):
        """
        Initialize a calendar day with empty shifts.

        Args:
            date (int): The calendar date.
        """
        self.date = date
        self.weekend = self.date.weekday() in {5, 6}  # True if Saturday or Sunday
        self.shifts = {"s1": None, "s2": None, "s3": None, "s4": None}

    def is_shift_filled(self, shift_type):
        """
        Check if a specific shift is filled.

        Args:
            shift_type (str): The shift type ('s1', 's2', 's3', 's4').

        Returns:
            bool: True if the shift is filled, False otherwise.
        """
        return self.shifts[shift_type] is not None

    def assign_shift(self, shift_type, doctor):
        """
        Assign a doctor to a specific shift.

        Args:
            shift_type (str): The shift type ('s1', 's2', 's3', 's4').
            doctor (Doctor): The doctor being assigned.

        Returns:
            bool: True if the assignment was successful, False otherwise.
        """
        if not self.is_shift_filled(shift_type):
            self.shifts[shift_type] = doctor
            return True
        return False

    def __repr__(self):
        assigned = {shift: doc.name if doc else None for shift, doc in self.shifts.items()}
        return f"<CalendarDay {self.date} - Assignments: {assigned}>"