from models import *
from datetime import date, timedelta

class Scheduler:
    def __init__(self, doctors, calendar):
        """
        Initialize the scheduler with doctors, a calendar, and optional previous month data.

        Args:
            doctors (list): List of Doctor objects.
            calendar (list): List of CalDay objects for the month.
            previous_month_data (dict): Optional data for shifts from the last 4 days of the previous month.
        """
        self.doctors = doctors
        self.calendar = calendar
        self.last_doctor_shift4 = None

        self.set_initial_last_shift4()

    def set_initial_last_shift4(self):
        """
        Determine the last doctor (other than PAT) who worked a 4 shift in the previous month.
        If no such doctor is found, prompt the user for input.
        """
        all_last_month_4shifts = []

        # Collect all previous month 4-shifts across all doctors
        for doctor in self.doctors:
            for shift_date, shift_type in doctor.previous_month_shifts:
                if shift_type == 4:  # Only consider 4 shifts
                    all_last_month_4shifts.append((shift_date, doctor))

        # Sort all 4-shifts by date (latest first)
        all_last_month_4shifts.sort(key=lambda x: x[0], reverse=True)

        # Find the most recent 4-shift worked by a doctor other than PAT
        for shift_date, doctor in all_last_month_4shifts:
            if doctor.name != "PAT":
                self.last_doctor_shift4 = doctor
                #print(f"Automatically set last_doctor_shift4 to {doctor.name} (worked last 4 shift on {shift_date})")
                return  # Exit early once the most recent non-PAT doctor is found

        while True: #prompt user for a doctor if PAT worked all 4 previous 4-shifts
            user_input = input("Enter the name of the doctor (other than PAT) who most recently worked a 4 shift: ").strip()
            
            # Check if the input matches a doctor in the list
            matching_doctors = [doc for doc in self.doctors if doc.name.lower() == user_input.lower()]
            if matching_doctors:
                self.last_doctor_shift4 = matching_doctors[0]
                break
            else:
                print("Error: doctor not recognized. Is this really that hard for you? I'm amazed you've even made it this far. Make sure you input a name from the list of doctors:")
                for doc in self.doctors:
                    print(f" - {doc.name}")
    
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

                        if self.assign_shift(cal_day, pat, "s4"):
                            days_scheduled += 1
                            last_shift_date = cal_day.date
                            consecutive_days += 1
                            #print(f"Day {cal_day.date}: Shift 4 assigned to PAT (extending previous cluster).")
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

                if self.assign_shift(current_day, pat, "s4"):
                    days_scheduled += 1
                    last_shift_date = current_day.date
                    #print(f"Day {current_day.date}: Shift 4 assigned to PAT.")

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
        Schedule the remaining shift 4s for doctors after PAT has been scheduled.
        If PAT is not scheduled early and a doctor other than PAT worked the last 4-shift of the previous month,
        that doctor will be prioritized for the first shift-4 cluster of the month.
        """
        pat_cluster_gaps = self.identify_pat_gaps()

        # Ensure that PAT is not scheduled on the first day of the month
        first_day_of_month = self.calendar[0]
        pat_scheduled_first_day = first_day_of_month.shifts["s4"] and first_day_of_month.shifts["s4"].name == "PAT"

        # Check if PAT worked the last shift-4 of the previous month
        last_day_prev_month = max((shift_date for doc in self.doctors for shift_date, shift_type in doc.previous_month_shifts if shift_type == 4), default=None)

        if last_day_prev_month:
            last_shift_doc = next((doc for doc in self.doctors if (last_day_prev_month, 4) in doc.previous_month_shifts), None)
            pat_scheduled_last_day = last_shift_doc and last_shift_doc.name == "PAT"
        else:
            pat_scheduled_last_day = False  # No shift data available, assume PAT was not scheduled

        # If PAT is NOT scheduled on the first day AND NOT scheduled on the last day of the previous month AND last doctor was not PAT, prioritize that doctor
        if not pat_scheduled_first_day and not pat_scheduled_last_day and self.last_doctor_shift4 and self.last_doctor_shift4.name != "PAT":
            first_gap = pat_cluster_gaps[0] if pat_cluster_gaps else None

            if first_gap:
                gap_start, gap_size = first_gap

                # Fetch doctor's previous month shift count
                last_doc_prev_shift_count = sum(1 for shift_date, shift_type in self.last_doctor_shift4.previous_month_shifts if shift_type == 4)

                # Determine how many more shifts they should work in the first cluster
                max_additional_shifts = max(0, 3 - last_doc_prev_shift_count)  # Ensure they don’t exceed 3 shifts in a row

                # Try scheduling them if they are eligible
                if max_additional_shifts > 0:
                    gap_start_index = next(
                        (i for i, cal_day in enumerate(self.calendar) if cal_day.date == gap_start), None
                    )

                    if gap_start_index is not None:
                        cluster_days = self.calendar[gap_start_index:gap_start_index + max_additional_shifts]
                        
                        if self.is_doctor_eligible_for_cluster(self.last_doctor_shift4, cluster_days, max_additional_shifts):
                            for i, cal_day in enumerate(cluster_days):
                                if not cal_day.is_shift_filled("s4"):
                                    self.assign_shift(cal_day, self.last_doctor_shift4, "s4")

                            # Reduce the gap size accordingly
                            pat_cluster_gaps[0] = (cluster_days[-1].date + timedelta(days=1), gap_size - max_additional_shifts)

        # Proceed with normal scheduling for the remaining gaps
        for gap in pat_cluster_gaps:
            gap_start, gap_size = gap

            while gap_size > 0:
                cluster_sizes = self.determine_cluster_plan(gap_size)
                scheduled = False  # Flag to track if we scheduled a cluster

                for cluster_size in cluster_sizes:
                    gap_start_index = next(
                        (i for i, cal_day in enumerate(self.calendar) if cal_day.date == gap_start),
                        None
                    )
                    if gap_start_index is not None:
                        cluster_days = self.calendar[gap_start_index:gap_start_index + cluster_size]
                    else:
                        print(f"Error: gap_start {gap_start} not found in the calendar.")
                        break

                    # Try to find a doctor for the cluster
                    selected_doc = self.select_best_doctor_for_4cluster(cluster_days, cluster_size)

                    if selected_doc is None:
                        print(f"Could not schedule a cluster of size {cluster_size} starting on {gap_start}.")
                        continue

                    # Assign the doctor to all days in the cluster
                    for cal_day in cluster_days:
                        if cal_day.is_shift_filled("s4"):
                            continue

                        self.assign_shift(cal_day, selected_doc, "s4")
                        self.last_doctor_shift4 = selected_doc

                    # Update the gap information
                    gap_start = cluster_days[-1].date + timedelta(days=1)
                    gap_size -= cluster_size
                    scheduled = True
                    break  # Exit the loop once a cluster is scheduled

    def identify_pat_gaps(self):
        """
        Identify gaps between PAT's scheduled shifts in the calendar.

        Returns:
            list of tuples: Each tuple contains the start date of a gap and its size in days.
        """
        gaps = []
        last_pat_date = None

        # Find the first PAT shift
        pat_shift_dates = [
            cal_day.date
            for cal_day in self.calendar
            if cal_day.is_shift_filled("s4") and cal_day.shifts["s4"].name == "PAT"
        ]

        # Add a gap from the start of the calendar to the first PAT shift, if applicable
        if pat_shift_dates and pat_shift_dates[0] > self.calendar[0].date:
            gaps.append((self.calendar[0].date, (pat_shift_dates[0] - self.calendar[0].date).days))

        for cal_day in self.calendar:
            if cal_day.is_shift_filled("s4") and cal_day.shifts["s4"].name == "PAT":
                if last_pat_date and (cal_day.date - last_pat_date).days > 1:
                    gaps.append((last_pat_date + timedelta(days=1), (cal_day.date - last_pat_date).days - 1))
                last_pat_date = cal_day.date

        # If PAT's last shift doesn't reach the end of the calendar, capture the final gap
        if last_pat_date and last_pat_date < self.calendar[-1].date:
            gaps.append((last_pat_date + timedelta(days=1), (self.calendar[-1].date - last_pat_date).days))

        #print("Gaps: ", gaps)
        return gaps
    
    def select_best_doctor_for_4cluster(self, cluster_days, cluster_size):
        """
        Select the best doctor to fill a given cluster.
        """
        best_doctor = None
        available_doctors = self.get_available_doctors_for_shift4_cluster(cluster_days, cluster_size)
        #print(f"Available doctors: {[doc.name for doc in available_doctors]}")
        
        best_doctor = sorted(
            available_doctors,
            key=lambda doc: (
                -doc.shift_prefs[3],  # Higher shift preference for s4 is better
                doc == self.last_doctor_shift4,  # De-prioritize the last doctor to work s4 (True sorts after False)
                doc.last_shift_date.date if isinstance(doc.last_shift_date, CalDay) 
                else (doc.last_shift_date if isinstance(doc.last_shift_date, date) else date.min),  # Extract actual date
                doc.night_shifts, # Fewest night shifts scheduled
                doc.total_shifts  # Fewest shifts scheduled
            ),
        )[0]

        return best_doctor

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
    
    def is_doctor_eligible_for_cluster(self, doctor, cluster_days, cluster_size):
        """
        Check if a doctor is eligible to work a given cluster of shift 4 days.

        Args:
            doctor (Doctor): The doctor being checked.
            cluster_days (list of CalDay): Days in the cluster being scheduled.

        Returns:
            bool: True if the doctor is eligible, False otherwise.
        """
        # Check if the doctor has a shift preference for shift 4 greater than 0
        if doctor.shift_prefs[3] == 0:
            return False

        # Don't schedule PAT
        if doctor.name == "PAT":
            return False
        
        # Check if the doctor has the day off for any day in the cluster
        if any(day.date in doctor.days_off for day in cluster_days):
            return False

        # Check if the doctor has the following day off (to avoid breaking clusters)
        if any((day.date + timedelta(days=1)) in doctor.days_off for day in cluster_days):
            return False

        # Check if the doctor has reached their max shifts
        if (doctor.total_shifts + cluster_size) >= doctor.max_shifts:
            return False

        return True

    def get_available_doctors_for_shift4_cluster(self, cluster_days, cluster_size):
        """
        Generate a list of doctors who are eligible to work a given cluster of shift 4 days.

        Args:
            cluster_days (list of CalDay): Days in the cluster being scheduled.

        Returns:
            list of Doctor: Doctors who are eligible for the given cluster.
        """
        available_doctors = [doctor for doctor in self.doctors if self.is_doctor_eligible_for_cluster(doctor, cluster_days, cluster_size)]
        #print(f"DEBUG: Available doctors for cluster on {cluster_days[0].date.strftime('%b %d')} - {cluster_days[-1].date.strftime('%b %d')}: {[doc.name for doc in available_doctors]}")
        
        # Prevent scheduling more than 5 consecutive shifts
        filtered_doctors = []
        
        for doctor in available_doctors:
            # Count how many consecutive s4 shifts the doctor already has
            consecutive_s4_count = 0
            
            current_date = cluster_days[0].date - timedelta(days=1)  # Start from the previous day

            # Iterate backwards through the calendar
            while current_date >= self.calendar[0].date:
                cal_day = next((day for day in self.calendar if day.date == current_date), None)

                if not cal_day or cal_day.shifts.get("s4") != doctor:
                    break  # Stop if no s4 shift or a different doctor was scheduled

                consecutive_s4_count += 1
                current_date -= timedelta(days=1)

            # If adding this cluster would push them over 5 consecutive shifts, exclude them
            if consecutive_s4_count + cluster_size <= 5:
                filtered_doctors.append(doctor)

        if not filtered_doctors:
            #print(f"WARNING: No available doctors for s4 cluster {cluster_days[0].date.strftime('%b %d')} - {cluster_days[-1].date.strftime('%b %d')}")
            return available_doctors  # Fallback: Return all doctors to avoid crashing
        
        return filtered_doctors  # Updated return statement to use filtered list
    
    def assign_shift(self, cal_day, doctor, shift_type):
        """
        Assigns a doctor to a shift, ensuring both calendar and doctor records are updated.

        Args:
            cal_day (CalDay): The calendar day object where the shift is assigned.
            doctor (Doctor): The doctor being assigned to the shift.
            shift_type (str): The shift type ('s1', 's2', 's3', 's4').

        Returns:
            bool: True if the assignment was successful, False otherwise.
        """
        if cal_day.assign_shift(shift_type, doctor):  # Assign to the calendar first
            doctor.assign_shift(cal_day, shift_type)  # Assign to the doctor's record
            #print(f"DEBUG: Successfully assigned {doctor.name} to {shift_type} on {cal_day.date.strftime('%b %d')}")
            return True
        return False

    def schedule_remaining_shifts(self, num_shifts):
        """
        Schedule remaining shifts for the month based on the number of shifts per day.

        Args:
            num_shifts (int): Number of shifts to schedule (3 or 4).
        """
        # Define which shifts to schedule (excluding s4)
        shifts_to_schedule = ["s1", "s3"]
        if num_shifts == 4:
            shifts_to_schedule = ["s1", "s2", "s3"]
        
        for cal_day in self.calendar:
            # Schedule all shifts for this day
            for shift in shifts_to_schedule:
                if not cal_day.is_shift_filled(shift):  # Only schedule if not already filled
                    selected_doc = self.select_best_doctor_for_shift(cal_day, shift)
                    if selected_doc:
                        self.assign_shift(cal_day, selected_doc, shift)

            self.update_consecutive_shifts(cal_day.date)  # Update consecutive_shifts

    def select_best_doctor_for_shift(self, cal_day, shift):
        """
        Select the best available doctor for a given shift on a given day.

        Args:
            cal_day (CalDay): The calendar day for which we are assigning a shift.
            shift (str): The shift type ("s1", "s2", or "s3").

        Returns:
            Doctor or None: The best available doctor or None if no one is available.
        """
        best_doctor = None
        
        # Step 1: Filter out unavailable doctors
        available_doctors = self.get_available_doctors(cal_day, shift)

        # to debug sorting, print out sortable attributes
        # for doc in available_doctors:
        #     print(f"Doctor: {doc.name}, Consecutive: {doc.consecutive_shifts}, "
        #         f"Total Shifts: {doc.total_shifts}, Max Shifts: {doc.max_shifts}, "
        #         f"Shift Pref: {doc.shift_prefs[int(shift[1]) - 1]}, "
        #         f"Flip Shifts: {doc.flip_shifts}, "
        #         f"Shift Ratio: {doc.total_shifts / doc.max_shifts:.2f}")
            
        doctor_names = sorted(
            available_doctors,
            key=lambda doc: (
                doc.consecutive_shifts >= 4, # De-prioritize docs with consecutive shifts >= 4
                doc.total_shifts >= doc.max_shifts, # De-prioritize docs that have been scheduled for their max shifts
                -doc.shift_prefs[int(shift[1]) - 1],  # Higher preference for this shift is better
                doc.flip_shifts != "Yes", # Higher preference for doctors with Flip Shifts Requested (i.e., part-time docs)
                doc.total_shifts / doc.max_shifts,  # Prefer doctors who are farther from their max shift allocation
            )
        )

        doctor_names = [doc.name for doc in doctor_names]
                              
        #print(f"DEBUG: Date: {cal_day.date.strftime('%b %d')}, Shift: {shift}, Available Doctors: {', '.join(doctor_names) if doctor_names else 'None'}")

        if not available_doctors:
            print(f"WARNING: No available doctors for {shift} on {cal_day.date.strftime('%b %d')}")
            return None

        # Step 2: Sort doctors based on priority
        best_doctor = sorted(
            available_doctors,
            key=lambda doc: (
                doc.consecutive_shifts >= 4, # De-prioritize docs with consecutive shifts >= 4
                doc.total_shifts >= doc.max_shifts, # De-prioritize docs that have been scheduled for their max shifts
                -doc.shift_prefs[int(shift[1]) - 1],  # Higher preference for this shift is better
                doc.flip_shifts != "Yes", # Higher preference for doctors with Flip Shifts Requested (i.e., part-time docs)
                doc.total_shifts / doc.max_shifts,  # Prefer doctors who are farther from their max shift allocation
            )
        )[0]

        return best_doctor
    
    def get_available_doctors(self, cal_day, shift):
        """
        Get the list of doctors available for a given shift on a given day.

        Args:
            cal_day (CalDay): The calendar day for which we are determining availability.
            shift (str): The shift type ("s1", "s2", or "s3").

        Returns:
            List[Doctor]: A list of available doctors.
        """
        available_doctors = []

        for doc in self.doctors:
            # Skip if the doctor has the day off
            if cal_day.date in doc.days_off:
                continue

            # Skip if the doctor has no preference for this shift
            shift_index = int(shift[1]) - 1  # Convert "s1" -> index 0, "s2" -> index 1, etc.
            if doc.shift_prefs[shift_index] == 0:
                continue

            # Skip if doctor has already worked 5 consecutive shifts
            if doc.consecutive_shifts >= 5:
                continue

            # Check if doctor is already scheduled for another shift that day
            if any(scheduled_doc == doc for scheduled_doc in cal_day.shifts.values()):
                continue

            # Determine the date(s) we need to check for past shifts
            prev_day = cal_day.date - timedelta(days=1)
            two_days_ago = cal_day.date - timedelta(days=2)

            # Look up the previous day's shift from the calendar if within the same month
            prev_day_obj = next((d for d in self.calendar if d.date == prev_day), None)

            # If the day is outside the calendar (first day of the month), check previous month shifts
            prev_day_s2_or_s3 = False
            if prev_day_obj:
                prev_day_s2_or_s3 = prev_day_obj.shifts.get("s2") == doc or prev_day_obj.shifts.get("s3") == doc
            else:
                # If no prev_day_obj exists, check previous month's shift history
                if (prev_day, "s2") in doc.previous_month_shifts or (prev_day, "s3") in doc.previous_month_shifts:
                    prev_day_s2_or_s3 = True

            # Skip doctor if they worked a later shift the previous day
            if shift == "s1" and prev_day_s2_or_s3:
                continue
            if shift == "s2" and prev_day_obj and prev_day_obj.shifts.get("s3") == doc:
                continue
            if shift == "s2" and not prev_day_obj and (prev_day, "s3") in doc.previous_month_shifts:
                continue

            # Look up 4-shifts from the last 2 days (across both calendar and previous month)
            last_2_days_s4 = False
            for check_date in [prev_day, two_days_ago]:
                past_day_obj = next((d for d in self.calendar if d.date == check_date), None)
                if past_day_obj and past_day_obj.shifts.get("s4") == doc:
                    last_2_days_s4 = True
                    break
                if (check_date, "s4") in doc.previous_month_shifts:
                    last_2_days_s4 = True
                    break

            # Skip doctor if they worked a 4-shift in either of the last 2 days
            if last_2_days_s4:
                continue

            # If none of the conditions exclude the doctor, add them to the list
            available_doctors.append(doc)

        # Step 1: Identify doctors scheduled the following day
        future_day = cal_day.date + timedelta(days=1)
        future_day_cal = next((d for d in self.calendar if d.date == future_day), None)
        
        # Step 2: Track consecutive days in the future
        future_consecutive_days = {}

        if future_day_cal:
            for doctor in available_doctors:
                count = 0
                next_day = future_day_cal

                while next_day and any(shift_doc == doctor for shift_doc in next_day.shifts.values()):
                    count += 1
                    next_day = next((d for d in self.calendar if d.date == next_day.date + timedelta(days=1)), None)

                future_consecutive_days[doctor] = count

        # Step 3: Remove doctors who would exceed 5 consecutive shifts
        available_doctors = [
            doctor for doctor in available_doctors
            if doctor.consecutive_shifts + 1 + future_consecutive_days.get(doctor, 0) <= 5
        ]

        return available_doctors
    
    def initialize_consecutive_shifts_from_previous_month(self):
        """
        Initializes consecutive shift counts for each doctor based on their shifts at the end of the previous month.

        This function analyzes a doctor's previous month's shifts and determines how many consecutive days 
        they worked leading into the first day of the new month.
        """
        for doctor in self.doctors:
            consecutive_days = 0

            # Sort shifts by date to process them in order
            sorted_shifts = sorted(doctor.previous_month_shifts, key=lambda x: x[0])

            for i in range(len(sorted_shifts) - 1, -1, -1):  # Iterate backwards from last shift
                shift_date, shift_type = sorted_shifts[i]

                if i == len(sorted_shifts) - 1:
                    # If the last shift is not on the last day of the month, break
                    if (self.calendar[0].date - shift_date).days > 1:
                        break

                # If the shift was the day before the first day of the new month, start counting
                if (self.calendar[0].date - shift_date).days == 1 + consecutive_days:
                    consecutive_days += 1
                else:
                    break  # Stop if there's a gap

            # Set the initial consecutive shift count for the doctor
            doctor.consecutive_shifts = consecutive_days

        # for doctor in self.doctors:
        #     print(f"Doctor: {doctor.name}, Consecutive Shifts: {doctor.consecutive_shifts}")

    def update_consecutive_shifts(self, current_date):
        """
        Updates consecutive shift counts for all doctors based on whether they worked on the given date.

        Args:
            current_date (datetime.date): The date for which scheduling has been completed.
        """
        doctors_who_worked_today = set()

        # Identify doctors scheduled on the given date
        for cal_day in self.calendar:
            if cal_day.date == current_date:
                for shift in cal_day.shifts.values():
                    if shift:  # If a doctor was assigned to any shift
                        doctors_who_worked_today.add(shift)  # Add doctor object

        # Increment consecutive shifts for doctors who worked today
        for doctor in doctors_who_worked_today:
            doctor.consecutive_shifts += 1

        # Reset consecutive shifts for doctors who did NOT work today
        for doctor in self.doctors:
            if doctor not in doctors_who_worked_today:
                doctor.consecutive_shifts = 0