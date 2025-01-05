from datetime import date, timedelta

class Doctor:
    def __init__(self, name, days_off, shift_prefs, min_shifts, max_shifts, priority=0, previous_month_shifts=None):
        """
        Initialize a doctor with their attributes.

        Args:
            name (str): Doctor's name.
            days_off (list): Days the doctor cannot work.
            shift_prefs (list): Preferred shifts (1, 2, 3, 4).
            min_shifts (int): Minimum shifts the doctor wants to work.
            max_shifts (int): Maximum shifts the doctor can work.
            priority (int): Calculated dynamic priority.
            previous_month_shifts (list): Shifts worked in the last 3 days of the previous month.
        """
        self.name = name
        self.days_off = {day if isinstance(day, date) else date(2024, 1, day) for day in days_off}
        self.shift_prefs = shift_prefs
        self.min_shifts = min_shifts
        self.max_shifts = max_shifts
        self.total_shifts = 0
        self.night_shifts = 0
        self.weekend_shifts = 0
        self.consecutive_shifts = 0
        self.priority = priority
        self.previous_month_shifts = [
            (day if isinstance(day, date) else date(2023, 12, day), shift_type)
            for day, shift_type in (previous_month_shifts or [])
        ]

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

    def assign_shift(self, date, shift_type, is_weekend=False):
        """
        Assign the doctor to a shift and update their statistics.

        Args:
            date (int): The current date.
            shift_type (int): The shift type (1, 2, 3, or 4).
            is_weekend (bool): Whether the shift is on a weekend.
        """
        self.total_shifts += 1
        if shift_type == 4:
            self.night_shifts += 1
        if is_weekend:
            self.weekend_shifts += 1
        self.consecutive_shifts += 1


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


# class Gap:
#     def __init__(self,start_date,length):
#         self.start_date = start_date
#         self.length = length
#         self.remaining = length
#         self.filled = False
#         self.docs = []