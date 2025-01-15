from models import *
from datetime import date, timedelta

import numpy as np
from columnar import columnar

class Scheduler:
    def __init__(self, doctors, calendar, previous_month_data=None):
        """
        Initialize the scheduler with doctors, a calendar, and optional previous month data.

        Args:
            doctors (list): List of Doctor objects.
            calendar (list): List of CalDay objects for the month.
            previous_month_data (dict): Optional data for shifts from the last 3 days of the previous month.
        """
        self.doctors = doctors
        self.calendar = calendar
        self.previous_month_data = previous_month_data or {}

        # Update doctors with previous month data if provided
        for doc in self.doctors:
            if doc.name in self.previous_month_data:
                doc.previous_month_shifts = self.previous_month_data[doc.name]
    
    def schedule_pat(self):
        """
        Schedule PAT for shift 4, enforcing minimum cluster size of 3 days.
        """
        pat = next(doc for doc in self.doctors if doc.name == "PAT")
        days_scheduled = 0
        last_shift_date = None
        consecutive_days = 0

        # If PAT has shifts at the end of the previous month, set consecutive days properly
        if pat.previous_month_shifts:
            last_shift_date = pat.previous_month_shifts[-1][0]
            previous_month = last_shift_date.month
            previous_year = last_shift_date.year
            if previous_month == 12:  # Handle December to January transition
                last_day_previous_month = date(previous_year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day_previous_month = date(previous_year, previous_month + 1, 1) - timedelta(days=1)

            # Check if the last few days of the previous month form a cluster
            if last_day_previous_month == last_shift_date:
                consecutive_days = 1
                for i in range(len(pat.previous_month_shifts) - 2, -1, -1):
                    if (pat.previous_month_shifts[i][0] - pat.previous_month_shifts[i + 1][0]).days == -1:
                        consecutive_days += 1
                    else:
                        break

        #print(f"PAT finished the previous month with a cluster of {consecutive_days} consecutive days.")
        #print(f"Initial last shift date: {last_shift_date}\n")
        #print("Scheduling PAT...")

        index = 0
        while index < len(self.calendar):
            cal_day = self.calendar[index]

            # Extend the cluster from the previous month, if applicable
            if last_shift_date and consecutive_days > 0:
                while index < len(self.calendar):
                    cal_day = self.calendar[index]

                    # Check if we can extend the cluster
                    if (cal_day.date - last_shift_date).days == 1 and cal_day.date not in pat.days_off and not cal_day.is_shift_filled("s4"):
                        if consecutive_days >= 4:
                            #print("Cluster has reached the maximum size of 4 days. Stopping extension.\n")
                            break

                        if cal_day.assign_shift("s4", pat):
                            pat.assign_shift(cal_day.date, 4, cal_day.weekend)
                            days_scheduled += 1
                            last_shift_date = cal_day.date
                            consecutive_days += 1
                            print(f"Day {cal_day.date}: Shift 4 assigned to PAT (extending previous cluster).")
                    else:
                        #print("Cluster extension complete. Transitioning to new scheduling.\n")
                        break

                    index += 1

            # Reset cluster tracking after extending
            if consecutive_days >= 4:
                consecutive_days = 0

            # Skip if PAT cannot work this day
            if cal_day.date in pat.days_off:
                #print(f"Skipping {cal_day.date}: PAT has the day off.")
                index += 1
                continue
            if cal_day.is_shift_filled("s4"):
                #print(f"Skipping {cal_day.date}: Shift 4 is already filled.")
                index += 1
                continue
            if last_shift_date and (cal_day.date - last_shift_date).days < 4:
                #print(f"Skipping {cal_day.date}: Not enough gap since last shift on {last_shift_date}.")
                index += 1
                continue

            # Determine cluster size
            remaining_shifts = pat.max_shifts - pat.total_shifts
            cluster_size = self.get_optimal_cluster_size(pat, index, remaining_shifts)

            # Enforce minimum cluster size of 3 days, except at the end of the month
            if cluster_size and cluster_size < 3:
                if index + cluster_size >= len(self.calendar):
                    # Allow smaller cluster at the end of the month
                    #print(f"Allowing smaller cluster of {cluster_size} days at the end of the month.")
                    pass
                else:
                    #print(f"Skipping {cal_day.date}: Cluster size {cluster_size} is too small.")
                    index += 1
                    continue

            # Schedule the cluster
            for j in range(cluster_size):
                if index + j >= len(self.calendar):
                    break

                current_day = self.calendar[index + j]
                if current_day.date in pat.days_off or current_day.is_shift_filled("s4"):
                    break

                if current_day.assign_shift("s4", pat):
                    pat.assign_shift(current_day.date, 4, current_day.weekend)
                    days_scheduled += 1
                    last_shift_date = current_day.date
                    print(f"Day {current_day.date}: Shift 4 assigned to PAT.")

            # Skip past the scheduled cluster
            index += cluster_size

        #print(f"\nScheduled PAT for {days_scheduled} shifts.")


    def can_start_cluster(self, pat, start_index, min_days):
        """
        Check if a cluster can start at the given index with the minimum required days.

        Args:
            pat (Doctor): The doctor being scheduled.
            start_index (int): The index of the calendar day to start from.
            min_days (int): The minimum number of days required for the cluster.

        Returns:
            bool: True if the cluster can start, False otherwise.
        """
        for j in range(min_days):
            if start_index + j >= len(self.calendar):  # Out of bounds
                return False
            cal_day = self.calendar[start_index + j]
            if cal_day.date in pat.days_off or cal_day.is_shift_filled("s4"):
                return False

        # Check for sufficient gap after the cluster
        next_available_day = start_index + min_days + 3
        if next_available_day < len(self.calendar):
            if not self.can_start_cluster(pat, next_available_day, 3):
                return False

        return True

    def get_optimal_cluster_size(self, pat, start_index, remaining_shifts=None):
        """
        Determine the optimal cluster size for PAT starting at a given index.
        """
        if remaining_shifts is None:
            remaining_shifts = pat.max_shifts - pat.total_shifts

        cluster_size = 0

        for i in range(start_index, len(self.calendar)):
            cal_day = self.calendar[i]

            if cal_day.date in pat.days_off:
                break
            if cal_day.is_shift_filled("s4"):
                break
            if cluster_size >= remaining_shifts:
                break

            cluster_size += 1

            # Stop cluster if it exceeds 4 shifts
            if cluster_size >= 4:
                break

        return cluster_size if cluster_size > 0 else None

    def schedule_remaining_shift4(self):
        """
        Schedule the remaining s4 shifts for doctors.
        """
        pat_cluster_gaps = self.identify_pat_gaps()

        print("PAT Cluster Gaps:")
        for gap in pat_cluster_gaps:
            print(f"Gap: {gap}, Start: {gap[0]}, Size: {gap[1]}, Type of Size: {type(gap[1])}")
            gap_start, gap_size = gap

            # Define cluster sizes based on gap size
            cluster_sizes = self.determine_cluster_plan(gap_size)

            for cluster_size in cluster_sizes:
                gap_start_index = next(
                    (i for i, cal_day in enumerate(self.calendar) if cal_day.date == gap_start),
                    None
                )
                if gap_start_index is not None:
                    cluster_days = self.calendar[gap_start_index:gap_start_index + cluster_size]
                else:
                    print(f"Error: gap_start {gap_start} not found in the calendar.")
                    continue

                # Try to find a doctor for the cluster
                selected_doc = self.select_best_doctor_for_cluster(cluster_days)

                if selected_doc is None:
                    # No eligible doctor found for this cluster size
                    print(f"Could not schedule a cluster of size {cluster_size} starting on {gap_start}.")
                    continue

                # Assign the doctor to all days in the cluster
                for cal_day in cluster_days:
                    if cal_day.is_shift_filled("s4"):
                        continue

                    # Assign the shift and update the doctor's consecutive shifts
                    cal_day.shifts["s4"] = selected_doc
                    selected_doc.increment_consecutive_shifts()

                # Break the loop once a valid cluster is scheduled
                break

    def identify_pat_gaps(self):
        """
        Identify gaps between PAT's scheduled shifts in the calendar.

        Returns:
            list of tuples: Each tuple contains the start date of a gap and its size in days.
        """
        gaps = []
        last_pat_date = None

        for cal_day in self.calendar:
            if cal_day.is_shift_filled("s4") and cal_day.shifts["s4"].name == "PAT":
                if last_pat_date and (cal_day.date - last_pat_date).days > 1:
                    gaps.append((last_pat_date + timedelta(days=1), (cal_day.date - last_pat_date).days - 1))
                last_pat_date = cal_day.date

        # If PAT's last shift doesn't reach the end of the calendar, capture the final gap
        if last_pat_date and last_pat_date < self.calendar[-1].date:
            gaps.append((last_pat_date + timedelta(days=1), (self.calendar[-1].date - last_pat_date).days))

        return gaps

    def determine_cluster_plan(self, gap_size):
        """
        Determine the ideal cluster plan based on the gap size (X).
        """
        if gap_size == 1:
            return [1]
        elif gap_size == 2:
            return [2, 1, 1]
        elif gap_size == 3:
            return [3, 2, 1, 1, 1]
        elif gap_size == 4:
            return [4, 3, 2, 2, 1, 1, 1, 1]
        elif gap_size == 5:
            return [3, 2, 4, 2, 2, 1, 3, 1, 1, 1, 1, 1]
        else:
            # General case for larger gaps, prioritize clusters of 3, then 4, then 2, and avoid size 1.
            plan = []
            while gap_size > 0:
                if gap_size >= 3:
                    plan.append(3)
                    gap_size -= 3
                elif gap_size >= 4:
                    plan.append(4)
                    gap_size -= 4
                elif gap_size >= 2:
                    plan.append(2)
                    gap_size -= 2
                else:
                    plan.append(1)
                    gap_size -= 1
            return plan

    def select_best_doctor_for_cluster(self, cluster_days):
        """
        Select the best doctor to fill a given cluster.
        """
        best_doctor = None
        best_priority = float('-inf')

        for doctor in self.doctors:
            if not self.is_doctor_eligible_for_cluster(doctor, cluster_days):
                continue

            # Calculate prioritization score
            priority_score = (
                doctor.shift_prefs[3],  # Preference for shift 4
                self.calculate_cluster_potential(doctor, cluster_days),  # Avoid 1-day clusters
                self.get_last_shift4_recency(doctor),  # Least recent shift 4 first
                doctor.max_shifts - doctor.shifts_scheduled  # Farthest from max shifts
            )

            if priority_score > best_priority:
                best_priority = priority_score
                best_doctor = doctor

        return best_doctor
    
    def is_doctor_eligible_for_cluster(self, doctor, cluster_days):
        """
        Check if a doctor is eligible to work all days in the given cluster.
        """
        for cal_day in cluster_days:
            if cal_day.date in doctor.days_off or (cal_day.date + timedelta(days=1)) in doctor.days_off:
                return False
            if doctor.shift_prefs[3] == 0:  # Strong dislike for shift 4
                return False
            if doctor.total_shifts >= doctor.max_shifts:
                return False
        return True