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

######################################################################

# def read_input(fname): #read Excel and create Doctor objects
#     docs = []
#     wb = xlrd.open_workbook(fname)
#     sheet = wb.sheet_by_name("Shift Prefs")
#     month = int(sheet.cell_value(1,1))
#     year = int(sheet.cell_value(1,2))
#     n = sheet.nrows
#     num_days = calendar.monthrange(year,month)[1]
#     for i in range(2, n):
#         name = sheet.cell_value(i,4).strip().upper()
#         min_shifts = list(map(int, re.split(r'\s|,\s',sheet.cell_value(i,5).strip())))[0]
#         max_shifts = list(map(int, re.split(r'\s|,\s',sheet.cell_value(i,5).strip())))[1]
#         if sheet.cell_value(i,6):
#             if sheet.cell_value(i,15):
#                 if len(sheet.cell_value(i,6).strip()) <= 1:
#                     days_on = [int(sheet.cell_value(i,6).strip())]
#                 else:
#                     days_on = list(map(int, re.split(r'\s|,\s',sheet.cell_value(i,6).strip())))
#                 days_off = [day for day in range(1,num_days+1) if day not in days_on]
#             else:
#                 if len(sheet.cell_value(i,6).strip()) <= 1:
#                     days_off = [int(sheet.cell_value(i,6).strip())]
#                 else:
#                     days_off = list(map(int, re.split(r'\s|,\s',sheet.cell_value(i,6).strip())))
#         else:
#             if sheet.cell_value(i,15):
#                 days_off = [day for day in range(1,num_days+1)]
#             else:
#                 days_off = []
#         shift_prefs = list(map(int, re.split(r'\s|,\s',sheet.cell_value(i,11).strip())))
#         doc = Doctor(name, days_off, shift_prefs, min_shifts, max_shifts)
#         docs.append(doc)
#     cal1 = CalDay(-3)
#     cal2 = CalDay(-2)
#     cal3 = CalDay(-1)
#     startCal(docs, sheet, n, cal1,cal2,cal3)
        
#     return docs, month, year, cal1, cal2, cal3

# def startCal(docs, sheet, n, cal1, cal2, cal3):  #read in and create Calendar days for last three days of previous month
#     for i in range(2, n):
#         if sheet.cell_value(i,12):
#             if int(sheet.cell_value(i,12)) == 1:
#                 cal1.s1 = docs[i-2]
#             elif int(sheet.cell_value(i,12)) == 2:
#                 cal1.s2 = docs[i-2]
#             elif int(sheet.cell_value(i,12)) == 3:
#                 cal1.s3 = docs[i-2]
#             elif int(sheet.cell_value(i,12)) == 4:
#                 cal1.s4 = docs[i-2]
#     for i in range(2, n):
#         if sheet.cell_value(i,13):
#             if int(sheet.cell_value(i,13)) == 1:
#                 cal2.s1 = docs[i-2]
#             elif int(sheet.cell_value(i,13)) == 2:
#                 cal2.s2 = docs[i-2]
#             elif int(sheet.cell_value(i,13)) == 3:
#                 cal2.s3 = docs[i-2]
#             elif int(sheet.cell_value(i,13)) == 4:
#                 cal2.s4 = docs[i-2]
#     for i in range(2, n):
#         if sheet.cell_value(i,14):
#             if int(sheet.cell_value(i,14)) == 1:
#                 cal3.s1 = docs[i-2]
#             elif int(sheet.cell_value(i,14)) == 2:
#                 cal3.s2 = docs[i-2]
#             elif int(sheet.cell_value(i,14)) == 3:
#                 cal3.s3 = docs[i-2]
#             elif int(sheet.cell_value(i,14)) == 4:
#                 cal3.s4 = docs[i-2]

# def printCal(docs,cal,year,month):
#     num_days = calendar.monthrange(year,month)[1]
#     firstDay = calendar.monthrange(year,month)[0]
#     if month > 1:
#         prevMonthDays = calendar.monthrange(year,month-1)[1]
#     else:
#         prevMonthDays = calendar.monthrange(year-1,12)[1]
#     if firstDay >= 2:
#         headers = [""]*(firstDay-2) +[str(prevMonthDays-2),str(prevMonthDays-1),str(prevMonthDays)] + list(map(str,range(1,num_days+1)))
#         shift1 = [""]*(firstDay-2)
#         shift2 = [""]*(firstDay-2)
#         shift3 = [""]*(firstDay-2)
#         shift4 = [""]*(firstDay-2)
#     else:
#         headers = [""]*(firstDay+5) +[str(prevMonthDays-2),str(prevMonthDays-1),str(prevMonthDays)] + list(map(str,range(1,num_days+1)))
#         shift1 = [""]*(firstDay+5)
#         shift2 = [""]*(firstDay+5)
#         shift3 = [""]*(firstDay+5)
#         shift4 = [""]*(firstDay+5)
#     for day in cal:
#         shift1.append(day.s1.name)
#         shift2.append(day.s2.name)
#         shift3.append(day.s3.name)
#         shift4.append(day.s4.name)
#     if firstDay >= 2:
#         printDays = num_days + firstDay - 2 + 3
#     else:
#         printDays = num_days + firstDay + 3 + 4
#     printRange = math.ceil(printDays/7)
#     printRange = printRange * 7
#     for i in range(0,printRange,7):
#         start = 0 + i
#         stop = min(7 + i, len(headers))
#         heads = headers[start:stop]
#         data = [shift1[start:stop],shift2[start:stop],shift3[start:stop],shift4[start:stop]]
#         print(columnar(data,heads,no_borders=True))
#         print()
#     for doc in docs:
#         print(doc.name + ": " + str(doc.shifts+doc.four_shifts) + " total shifts and " + str(doc.weekends) + " weekend shifts.")
#     print()

# def buildCal(docs, cal, num_days, year, month, fname):
#     os.system("cls||clear")
#     print()
#     last3days(docs,cal)
#     inp = input("Type 'Y' to make a new schedule from scratch, and type 'N' to only schedule the day shifts: ").strip().upper()
#     while inp != "Y" and inp != "N":
#         inp = input("Geoff, you ignorant slut. Type 'Y' to make a new schedule from scratch, and type 'N' to only schedule the day shifts: ").strip().upper()
#     if inp == "Y":
#         schedule4Shifts(docs,cal,num_days) 
#         #check4Shifts(docs,cal,year,month)
#         #printCal(docs,cal,year,month)
#         exportCal(fname, cal, year, month)
#         os.system('cls||clear')
#         cmd = "start EXCEL.EXE " + fname
#         os.system(cmd)
#         print()
#         inp = input("When you're done setting the night shifts, save and close out of the Excel document. Press enter when you are ready to continue, you abominable nincompoop: ")

#     readInFourShifts(fname, docs, cal, year, month)
#     for doc in docs:
#         doc.four_shifts = 0
#         doc.weekends = 0
#     for i in range(3,len(cal)):
#         cal[i].s4.four_shifts += 1
#         if cal[i].weekend == True:
#             cal[i].s4.weekends += 1
        
#     for doc in docs:
#         doc.max_shifts -= doc.four_shifts
#         doc.min_shifts -= doc.four_shifts
#         doc.consec_shifts = 0
#     for i in range(3):
#         cal[i].s1.consec_shifts += 1
#         cal[i].s2.consec_shifts += 1
#         cal[i].s3.consec_shifts += 1
#         cal[i].s4.consec_shifts += 1
#         worked = [cal[i].s1,cal[i].s2,cal[i].s3,cal[i].s4]
#         notWorked = set(docs) - set(worked)
#         for doc in notWorked:
#             doc.consec_shifts = 0
    
#     for i in range(num_days):
#         date = i + 1
#         index = i + 3
#         schedule1Shift(docs,cal,index)
#         schedule2Shift(docs,cal,index)
#         schedule3Shift(docs,cal,index)
#         docsWorking = [cal[index].s1,cal[index].s2,cal[index].s3,cal[index].s4]
#         for doc in docs:
#             if doc in docsWorking:
#                 doc.consec_shifts += 1
#             else:
#                 doc.consec_shifts = 0
#     #printCal(docs,cal,year,month)

# def exportCal(fname,cal,year,month):
#     wb = openpyxl.load_workbook(fname)
#     sheet = wb["Color"]
#     for i in [5,6,7,8,12,13,14,15,19,20,21,22,26,27,28,29,33,34,35,36,41,42,43,44]:
#         for j in range(2,9):
#             sheet.cell(i,j).value = ""
#     firstDay = calendar.monthrange(year,month)[0]
#     startRow = 5
#     days = 3
#     col = firstDay + 3
#     if col > 8:
#         col -= 7
#     while days < len(cal):
#         if col > 8:
#             col -= 7
#             startRow += 7
#         sheet.cell(startRow, col).value = cal[days].s1.name
#         sheet.cell(startRow + 1,col).value = cal[days].s2.name
#         sheet.cell(startRow + 2,col).value = cal[days].s3.name
#         sheet.cell(startRow + 3,col).value = cal[days].s4.name
#         days += 1
#         col += 1
    
#     wb.save(fname)

# def readInFourShifts(fname,docs,cal,year,month):
#     wb = xlrd.open_workbook(fname)
#     sheet = wb.sheet_by_name("Color")
#     firstDay = calendar.monthrange(year,month)[0]
#     startRow = 4
#     days = 3
#     col = firstDay + 2
#     if col > 7:
#         col -= 7
#     while days < len(cal):
#         if col > 7:
#             col -= 7
#             startRow += 7
#         name = sheet.cell_value(startRow + 3, col).strip().upper()
#         for doc in docs:
#             if doc.name == name:
#                 cal[days].s4 = doc
#         days += 1
#         col += 1