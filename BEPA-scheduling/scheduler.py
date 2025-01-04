from models import *
from datetime import date, timedelta

import calendar
import re
import numpy as np
from columnar import columnar
import random
import os

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

        print(f"PAT finished the previous month with a cluster of {consecutive_days} consecutive days.")

        print(f"Initial last shift date: {last_shift_date}\n")
        print("Scheduling PAT...")

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
                            print("Cluster has reached the maximum size of 4 days. Stopping extension.\n")
                            break

                        if cal_day.assign_shift("s4", pat):
                            pat.assign_shift(cal_day.date, 4, cal_day.weekend)
                            days_scheduled += 1
                            last_shift_date = cal_day.date
                            consecutive_days += 1
                            print(f"Day {cal_day.date}: Shift 4 assigned to PAT (extending previous cluster).")
                    else:
                        print("Cluster extension complete. Transitioning to new scheduling.\n")
                        break

                    index += 1

            # Reset cluster tracking after extending
            if consecutive_days >= 4:
                consecutive_days = 0

            # Skip if PAT cannot work this day
            if cal_day.date in pat.days_off:
                print(f"Skipping {cal_day.date}: PAT has the day off.")
                index += 1
                continue
            if cal_day.is_shift_filled("s4"):
                print(f"Skipping {cal_day.date}: Shift 4 is already filled.")
                index += 1
                continue
            if last_shift_date and (cal_day.date - last_shift_date).days < 4:
                print(f"Skipping {cal_day.date}: Not enough gap since last shift on {last_shift_date}.")
                index += 1
                continue

            # Determine cluster size
            remaining_shifts = pat.max_shifts - pat.total_shifts
            cluster_size = self.get_optimal_cluster_size(pat, index, remaining_shifts)

            # Enforce minimum cluster size of 3 days, except at the end of the month
            if cluster_size and cluster_size < 3:
                if index + cluster_size >= len(self.calendar):
                    # Allow smaller cluster at the end of the month
                    print(f"Allowing smaller cluster of {cluster_size} days at the end of the month.")
                else:
                    print(f"Skipping {cal_day.date}: Cluster size {cluster_size} is too small.")
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

        print(f"\nScheduled PAT for {days_scheduled} shifts.")


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



#################################################################################################
def last3days(docs,cal):  #sets consec_shifts for docs based on last three days of work
    for i in range(3):
        cal[i].s1.consec_shifts += 1
        cal[i].s2.consec_shifts += 1
        cal[i].s3.consec_shifts += 1
        cal[i].s4.consec_shifts += 1
        worked = [cal[i].s1,cal[i].s2,cal[i].s3,cal[i].s4]
        notWorked = set(docs) - set(worked)
        for doc in notWorked:
            doc.consec_shifts = 0

def schedule1Shift(docs,cal,index):
    date = index - 2
    P0 = docs[:]
    for doc in docs: #if doc scheduled a day off, or worked a later shift the day before, or have worked 4 consecutive shifts, or have worked over their max shifts, remove them
        if doc.name == "ADAL" or doc.name == "COL" or doc.name == "PAT" or date in doc.days_off or cal[index].s4 == doc or cal[index - 1].s2 == doc or cal[index - 1].s3 == doc or cal[index - 1].s4 == doc or doc.consec_shifts >= 4 or doc.shifts >= doc.max_shifts or (cal[min(index+1,len(cal)-1)].s4 == doc and doc.consec_shifts != 0) or cal[index - 2].s4 == doc or (doc.name == "HRA" and doc.consec_shifts >=3):
            P0.remove(doc)
    P1 = [doc for doc in P0 if doc.consec_shifts <= 4 and doc.shifts < doc.min_shifts and doc.lastSixDays < 5 and doc.lastNineDays < 7]
    P2 = [doc for doc in P0 if doc not in P1 and doc.lastSixDays < 5 and doc.lastNineDays < 7]
    P3 = [doc for doc in P0 if doc not in P1 and doc not in P2]
    if len(P1) > 1:
        P1.sort(key = lambda x: x.min_shifts, reverse = True)
        P1.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P1.sort(key = lambda x: x.weekends)
        P1.sort(key = lambda x: x.shift_prefs[0], reverse = True)

    if len(P1) >= 1:
        schedDoc = P1[0]
    
    elif len(P2) >= 1:
        P2.sort(key = lambda x: x.min_shifts, reverse = True)
        P2.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P2.sort(key = lambda x: x.weekends)
        P2.sort(key = lambda x: x.shift_prefs[0], reverse = True)
        schedDoc = P2[0]

    elif len(P3) >= 1:
        P3.sort(key = lambda x: x.min_shifts, reverse = True)
        P3.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P3.sort(key = lambda x: x.weekends)
        P3.sort(key = lambda x: x.shift_prefs[0], reverse = True)
        schedDoc = P3[0]

    else: 
        schedDoc = Doctor("--",[],[],0,0)
    """ print(str(date) + " shift 1: " + schedDoc.name)
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P1])
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P2])
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P3]) """
    cal[index].s1 = schedDoc
    schedDoc.shifts += 1
    if cal[index].weekend == True:
        schedDoc.weekends += 1

def schedule2Shift(docs,cal,index):
    date = index - 2
    P0 = docs[:]
    switchROD = False
    switchHRA = False
    for doc in docs: #if doc scheduled a day off, or worked a later shift the day before, or have worked 4 consecutive shifts, or have worked over their max shifts, remove them
        if doc.name == "ROTT" or doc.name == "PAT" or date in doc.days_off or cal[index].s4 == doc or cal[index].s1 == doc or cal[index - 1].s3 == doc or cal[index - 1].s4 == doc or doc.consec_shifts >= 4 or doc.shifts >= doc.max_shifts or (cal[min(index+1,len(cal)-1)].s4 == doc and doc.consec_shifts != 0) or cal[index - 2].s4 == doc or (doc.name == "HRA" and doc.consec_shifts >=3):
            P0.remove(doc)
    P1 = [doc for doc in P0 if doc.consec_shifts <= 4 and doc.shifts < doc.min_shifts and doc.lastSixDays < 5 and doc.lastNineDays < 7]
    P2 = [doc for doc in P0 if doc not in P1 and doc.lastSixDays < 5 and doc.lastNineDays < 7]
    P3 = [doc for doc in P0 if doc not in P1 and doc not in P2]

    if len(P1) > 1:
        P1.sort(key = lambda x: x.min_shifts, reverse = True)
        P1.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P1.sort(key = lambda x: x.weekends)
        P1.sort(key = lambda x: x.shift_prefs[1], reverse = True)

    if len(P1) >= 1:
        schedDoc = P1[0]
    
    elif len(P2) >= 1:
        P2.sort(key = lambda x: x.min_shifts, reverse = True)
        P2.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P2.sort(key = lambda x: x.weekends)
        P2.sort(key = lambda x: x.shift_prefs[1], reverse = True)
        schedDoc = P2[0]

    elif len(P3) >= 1:
        P3.sort(key = lambda x: x.min_shifts, reverse = True)
        P3.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P3.sort(key = lambda x: x.weekends)
        P3.sort(key = lambda x: x.shift_prefs[1], reverse = True)
        schedDoc = P3[0]

    else:
        schedDoc = Doctor("--",[],[],0,0)
    """ print(str(date) + " shift 2: " + schedDoc.name)
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P1])
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P2])
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P3]) """
    cal[index].s2 = schedDoc
    schedDoc.shifts += 1
    if cal[index].weekend == True:
        schedDoc.weekends += 1

def schedule3Shift(docs,cal,index):
    date = index - 2
    P0 = docs[:]
    for doc in docs: #if doc scheduled a day off, or worked a later shift the day before, or have worked 4 consecutive shifts, or have worked over their max shifts, remove them
        if doc.name == "ROTT" or doc.name == "COL" or doc.name == "ADAL" or doc.name == "PAT" or date in doc.days_off or cal[index].s4 == doc or cal[index].s1 == doc or cal[index].s2 == doc or cal[index - 1].s4 == doc or doc.consec_shifts >= 4 or doc.shifts >= doc.max_shifts or (cal[min(index+1,len(cal)-1)].s4 == doc and doc.consec_shifts != 0) or cal[index - 2].s4 == doc or (doc.name == "HRA" and doc.consec_shifts >=3):
            P0.remove(doc)
    if cal[index].s2.name == "ROD" or cal[index].s4.name == "ROD":
        for doc in P0:
            if doc.name == "HRA":
                P0.remove(doc)
    if cal[index].s2.name == "HRA" or cal[index].s4.name == "HRA":
        for doc in P0:
            if doc.name == "ROD":
                P0.remove(doc)            
    P1 = [doc for doc in P0 if doc.consec_shifts <= 4 and doc.shifts < doc.min_shifts and doc.lastSixDays < 5 and doc.lastNineDays < 7]
    P2 = [doc for doc in P0 if doc not in P1 and doc.lastSixDays < 5 and doc.lastNineDays < 7]
    P3 = [doc for doc in P0 if doc not in P1 and doc not in P2]
    if len(P1) > 1:
        P1.sort(key = lambda x: x.min_shifts, reverse = True)
        P1.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P1.sort(key = lambda x: x.weekends)
        P1.sort(key = lambda x: x.shift_prefs[2], reverse = True)

    if len(P1) >= 1:
        schedDoc = P1[0]
    
    elif len(P2) >= 1:
        P2.sort(key = lambda x: x.min_shifts, reverse = True)
        P2.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P2.sort(key = lambda x: x.weekends)
        P2.sort(key = lambda x: x.shift_prefs[2], reverse = True)
        schedDoc = P2[0]

    elif len(P3) >= 1:
        P3.sort(key = lambda x: x.min_shifts, reverse = True)
        P3.sort(key = lambda x: x.shifts/max(x.min_shifts,1))
        if cal[index].weekend == True:
            P3.sort(key = lambda x: x.weekends)
        P3.sort(key = lambda x: x.shift_prefs[2], reverse = True)
        schedDoc = P3[0]
    else:
        schedDoc = Doctor("--",[],[],0,0)
    """ print(str(date) + " shift 3: " + schedDoc.name)
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P1])
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P2])
    print([doc.name + " " + str(doc.shifts) + " " + str(doc.min_shifts) + " " + str(doc.lastSixDays) + " " + str(doc.lastNineDays) for doc in P3])
    print() """
    cal[index].s3 = schedDoc
    schedDoc.shifts += 1
    if cal[index].weekend == True:
        schedDoc.weekends += 1

        

def schedule4Shifts(docs,cal,num_days):
    P1 = [doc for doc in docs if doc.shift_prefs[3] == 9]
    P2 = [doc for doc in docs if doc.shift_prefs[3] == 8]
    P3 = [doc for doc in docs if doc.shift_prefs[3] == 7]
    P4 = [doc for doc in docs if doc.shift_prefs[3] <= 6]
    
    #schedule first few shifts of month based on who worked the end of last month
    date = 1
    os.system("cls||clear")
    print()
    pShifts = input("How many consecutive days was PAT's most recent series of night shifts? ")
    print()
    while(True):
        if pShifts.isdigit():
            pShifts = int(pShifts)
            if pShifts >= 0:
                break
        else:
            pShifts = input("That's not a valid response, jackass. How many consecutive days was PAT's most recent series of night shifts? ")
    if pShifts >= 4:
        minGap = 3
    else:
        minGap = 3

    if cal[2].s4 in P1:
        max_night_shifts = 4
    elif cal[2].s4 in P2:
        max_night_shifts = min(3,minGap)
    elif cal[2].s4 in P3:
        max_night_shifts = 2
    else:
        max_night_shifts = 1
    if cal[2].s4 != P1[0]:
        schedDoc = cal[2].s4
        #print(schedDoc.name + " " + str(schedDoc.consec_shifts) + " " + str(schedDoc.four_shifts))
        while schedDoc.consec_shifts < 3 and schedDoc.four_shifts < max_night_shifts - 1 and date not in schedDoc.days_off and date + 1 not in schedDoc.days_off:
            #print(schedDoc.name + " " + str(schedDoc.consec_shifts) + " " + str(schedDoc.four_shifts))
            cal[date + 2].s4 = schedDoc
            schedDoc.consec_shifts += 1
            schedDoc.four_shifts += 1
            if cal[date + 2].weekend == True:
                schedDoc.weekends += 1
            date += 1
    else:
        schedDoc = P1[0]
        while schedDoc.consec_shifts < 4 and date not in schedDoc.days_off and date + 1 not in schedDoc.days_off:
            cal[date + 2].s4 = schedDoc
            schedDoc.consec_shifts += 1
            schedDoc.four_shifts += 1
            if cal[date + 2].weekend == True:
                schedDoc.weekends += 1
            date += 1

    #schedule Patton
    if schedDoc == P1[0]:
        date += schedDoc.consec_shifts - 1
    shiftReset = P1[0].four_shifts
    weekendReset = P1[0].weekends
    schedDoc = P1[0]
    for i in range(date,num_days+1):
        index = i + 2
        if cal[index].s4.name == "--":
            lastDayIndex = i + 2
            while cal[lastDayIndex].s4 != P1[0]:  #find index of last day Patton had a shift
                if lastDayIndex == 0:
                    break
                else:
                    lastDayIndex -= 1
            gap = index - lastDayIndex
            #print("date: " + str(i) + " gap: " + str(gap))
            if gap > minGap:
                if list(set([i,i+1,i+2])&set(schedDoc.days_off)) == [] and list(set([i,i+1,i+2])) == []:
                    cal[index].s4 = schedDoc
                    if index+1 <= len(cal)-1:
                        cal[index+1].s4 = schedDoc
                        schedDoc.four_shifts += 2
                        if cal[index].weekend == True:
                            schedDoc.weekends += 1
                        if cal[index + 1].weekend == True:
                            schedDoc.weekends += 1
                    minGap = 3
                    if i+3 not in schedDoc.days_off:
                        if index+2 <= len(cal)-1:
                            cal[index + 2].s4 = schedDoc
                            schedDoc.four_shifts += 1
                            if cal[index + 2].weekend == True:
                                schedDoc.weekends += 1
                        minGap = 3
                        rand = random.randint(0,1)
                        if i+4 not in schedDoc.days_off and i+3 != num_days and rand == 1:
                            if index+3 <= len(cal)-1:
                                cal[index+3].s4 = schedDoc
                                schedDoc.four_shifts += 1
                                if cal[index + 3].weekend == True:
                                    schedDoc.weekends += 1
                                minGap = 3
        #print(str(i) + ": " + str(P1[0].four_shifts))

##    #if Patton does not have enough shifts
##    if P1[0].four_shifts < 0:
##        P1[0].four_shifts = shiftReset
##        P1[0].weekends = weekendReset
##        date -= 1
##        for i in range(date+2,len(cal)):
##            cal[i].s4 = Doctor("--",[],[],[],[],[],[],0,0)
##        minGap = 2
##        for i in range(date,num_days+1):
##            index = i + 2
##            if cal[index].s4.name == "--":
##                lastDayIndex = i + 2
##                while cal[lastDayIndex].s4 != P1[0]:  #find index of last day Patton had a shift
##                    if lastDayIndex == 0:
##                        break
##                    else:
##                        lastDayIndex -= 1
##                gap = index - lastDayIndex
##                if gap > minGap:
##                    if list(set([i,i+1,i+2])&set(schedDoc.days_off)) == [] and list(set([i,i+1,i+2])&set(schedDoc.FourSO)) == []:
##                        cal[index].s4 = schedDoc
##                        if index+1 <= len(cal)-1:
##                            cal[index+1].s4 = schedDoc
##                            schedDoc.four_shifts += 2
##                            if cal[index].weekend == True:
##                                schedDoc.weekends += 1
##                            if cal[index + 1].weekend == True:
##                                schedDoc.weekends += 1
##                        minGap = 2
##                        if i+3 not in schedDoc.days_off and i+3 not in schedDoc.FourSO:
##                            if index+2 <= len(cal)-1:
##                                cal[index + 2].s4 = schedDoc
##                                schedDoc.four_shifts += 1
##                                if cal[index + 2].weekend == True:
##                                    schedDoc.weekends += 1
##                            minGap = 2
##                            if i+4 not in schedDoc.days_off and i+4 not in schedDoc.FourSO and i+3 != num_days:
##                                if index+3 <= len(cal)-1:
##                                    cal[index+3].s4 = schedDoc
##                                    schedDoc.four_shifts += 1
##                                    if cal[index + 3].weekend == True:
##                                        schedDoc.weekends += 1
##                                minGap = 2     
    #Determine which doc worked most recent gap before first gap
    docNames = [doc.name for doc in docs]
    inp = input("Which docs (other than PAT) have worked night shifts in the 7 days leading up to this month? Separate multiple docs with a comma and space: ")
    lastDocsOG = re.split(r'\s|,\s',inp.strip().upper())
    while(True):
        arr = [name for name in lastDocsOG if name not in docNames]
        if len(arr) == 0:
            break
        else:
            inp = input("Error: doctor(s) not recognized. Is this really that hard for you? I'm amazed you've even made it this far. Make sure you spell them the same way as on the input sheet, and separate multiple docs with a comma and a space: ")
            lastDocsOG = re.split(r'\s|,\s',inp.strip().upper())   
    
    #Create GapMap
    gapMap = createGapMap(cal,num_days)
    #print([str(gap.start_date) + ", " + str(gap.length) for gap in gapMap])

    #KED and MIZ
    for i in range(len(gapMap)):
        gap = gapMap[i]
        gapDates = [gap.start_date + j for j in range(gap.length)]
        if gap.length >= 3:
            gapDocs = P2[:]
            for doc in gapDocs:
                if doc.four_shifts > 3:
                    gapDocs.remove(doc)
            gapDocs.sort(key = lambda x: x.four_shifts)
            schedule4Gaps(cal,gap,gapDocs,gapDates,3,lastDocsOG)

    #KED and MIZ and ROD and TOM
    gapMap = createGapMap(cal,num_days)
    #print([str(gap.start_date) + ", " + str(gap.length) for gap in gapMap])

    for i in range(len(gapMap)):
        gap = gapMap[i]
        gapDates = [gap.start_date + j for j in range(gap.length)]
        if gap.length >= 2:
            gapDocs = sorted(P3[:],key = lambda x: x.four_shifts) + sorted(P2[:], key = lambda x: x.four_shifts)
            if gap.length >= 3:
                gapDocs = sorted(P2[:],key = lambda x: x.four_shifts) + sorted(P3[:], key = lambda x: x.four_shifts)
            for doc in gapDocs:
                if doc.four_shifts > 4:
                    gapDocs.remove(doc)
            schedule4Gaps(cal,gap,gapDocs,gapDates,2,lastDocsOG)

    #ROD and TOM
    gapMap = createGapMap(cal,num_days)
    #print([str(gap.start_date) + ", " + str(gap.length) for gap in gapMap])

    for i in range(len(gapMap)):
        gap = gapMap[i]
        gapDates = [gap.start_date + j for j in range(gap.length)]
        gapDocs = P3[:]
        gapDocs.sort(key = lambda x: x.four_shifts)
        schedule4Gaps(cal,gap,gapDocs,gapDates,1,lastDocsOG)

                
def schedule4Gaps(cal,gap,gapDocs,gapDates,min_shifts,lastDocsOG):
    for doc in gapDocs:
        for i in range(len(gapDates)-min_shifts + 1):
            date = gapDates[i]
            index = date + 2
            lastDocs = []
            if index <= 6:
                lastDocs = lastDocsOG[:]
            else:
                for q in range(index - 7, min(index + 7,len(cal))):
                    lastDocs.append(cal[q].s4.name)
            if list(set(range(date,date+min_shifts+1))&set(doc.days_off)) == [] and list(set(range(date,date+min_shifts))) == [] and doc.name not in lastDocs:
                goSched = True
                for d in range(min_shifts):
                    if cal[index + d].s4.name != "--":
                        goSched = False
                """ print([doc.name for doc in gapDocs])
                print(lastDocs)
                print(str(date) + " " + str(gap.remaining) + " " + doc.name) """
                if goSched == True:
                    for j in range(min_shifts):
                        #print(str(index+j-2) + " " + doc.name)
                        cal[index + j].s4 = doc
                        doc.four_shifts += 1
                        gap.remaining -= 1
                        if cal[index + j].weekend == True:
                            doc.weekends += 1
                    gap.docs.append(doc)
                    #schedule additional shift
                    if gap.remaining > 0 and min_shifts != 3 and cal[min(index + min_shifts,len(cal)-1)].s4.name == "--" and not (min_shifts == 2 and (doc.name == "ROD" or doc.name == "TOM")):
                        if date + min_shifts not in doc.days_off and date + min_shifts + 1 not in doc.days_off:
                            cal[index + min_shifts].s4 = doc
                            doc.four_shifts += 1
                            gap.remaining -= 1
                            if cal[index + min_shifts].weekend == True:
                                doc.weekends += 1           
                    break

def createGapMap(cal, num_days):
    gapMap = []
    onGap = False
    gapLength = 0
    gapStart = 0
    for i in range(num_days):
        date = i+1
        index = i+3
        if onGap == False and cal[index].s4.name == "--":
            gapStart = date
            gapLength = 1
            onGap = True
        elif onGap == True and cal[index].s4.name == "--":
            gapLength += 1
        elif onGap == True and cal[index].s4.name != "--":
            gapMap.append(Gap(gapStart,gapLength))
            onGap = False
        if date == num_days and onGap == True:
            gapMap.append(Gap(gapStart, gapLength))
    return gapMap

def check4Shifts(docs,cal,year,month):
    from utils import printCal
    docNames = [doc.name for doc in docs]
    printCal(docs,cal,year,month)
    change = input("Would you like to make any 4-shift changes? Type 'Y' or 'N': ").strip().upper()
    while change != "Y" and change != "N":
        change = input("Invalid input. Would you like to make any 4-shift changes? Type 'Y' or 'N': ").strip().upper()
    if change == "N":
        print("\nGreat! I'll schedule the other shifts now, you lazy bum.\n")
    else:
        while True:
            date = input("\nWhich date would you like to change? Type date here: ").strip()
            while True: #get date to change
                if date.isdigit():
                    date = int(date)
                    if date > 0 and date <= calendar.monthrange(year,month)[1]:
                        break
                    else:
                        date = input("Not a valid date. Which date would you like to change? Type date here: ").strip()
                else:
                    date = input("Not a valid date. Which date would you like to change? Type date here: ").strip()
            
            while True: #get new doctor's name
                name = input("Which doctor would you like to take that shift? Type the doctor's name here, the same as it is in the input spreadsheet: ").strip().upper()
                while name not in docNames:
                    name = input("Invalid name. Be sure to spell the doctor's name the same way it is spelled in the input spreadsheet: ").strip().upper()
                index = date + 2
                doc_to_replace = cal[index].s4
                for doc in docs:
                    if doc.name == name:
                        replacement_doc = doc
                while date in replacement_doc.days_off or date + 1 in replacement_doc.days_off:
                    inp = input("This causes a scheduling conflict due to days that this doctor requested off. Is this ok? Type 'Y' or 'N': ").strip().upper()
                    if inp == 'Y':
                        break
                    else:
                        name = input("Which doctor would you like to take that shift? Type the doctor's name here, the same as it is in the input spreadsheet: ").strip().upper()
                        while name not in docNames:
                            name = input("Invalid name. Be sure to spell the doctor's name the same way it is spelled in the input spreadsheet: ").strip().upper()
                        for doc in docs:
                            if doc.name == name:
                                replacement_doc = doc


                doc_to_replace.four_shifts -= 1
                replacement_doc.four_shifts += 1
                if cal[index].weekend == True:
                    doc_to_replace.weekends -= 1
                    replacement_doc.weekends += 1
                cal[index].s4 = replacement_doc
                break
            
            printCal(docs,cal,year,month)
            change = input("\nWould you like to make any more 4-shift changes? Type 'Y' or 'N': ").strip().upper()
            while change != "Y" and change != "N":
                change = input("Invalid input. Would you like to make any additional 4-shift changes? Type 'Y' or 'N': ").strip().upper()
            if change == 'N':
                printCal(docs,cal,year,month)
                print("\nGreat! Here's the new schedule. I'll schedule the other shifts now, you lazy bum.\n")
                break