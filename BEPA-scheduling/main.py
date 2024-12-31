from utils import read_input, buildCal, exportCal, printCal
from scheduler import schedule1Shift, schedule4Shifts, check4Shifts
from models import Doctor, CalDay
import sys
import os
import calendar

def main():
    cal = calendar.TextCalendar()

    inp1 = input("Tu eres garbajo que muerte para dinero. Type 'yes' to agree with this statement: ")
    while inp1.lower().strip() != "yes":
        print()
        print("You absolute nincompoop. Can't you follow one simple instruction? Let's try again.")
        inp1 = input("Tu eres garbajo que muerte para dinero. Type 'yes' to agree with this statement: ")
    print()
    inp1 = input("Glad you agree. Now that that's settled, let's get to scheduling. Press enter to continue: ")
    os.system('cls||clear')

    fname = sys.argv[1]
    docs,month,year,cal1,cal2,cal3 = read_input(fname)
    schedule = []
    #print(cal.prmonth(2020,5))
    #print(calendar.monthrange(2020,8))
    num_days = calendar.monthrange(year,month)[1]
    DOYstart = calendar.monthrange(year,month)[0]
    schedule.append(cal1)
    schedule.append(cal2)
    schedule.append(cal3)
    for i in range(num_days):
        schedule.append(CalDay(i+1))
        weekendTracker = DOYstart + i
        while weekendTracker >= 7:
            weekendTracker -= 7
        if weekendTracker == 5 or weekendTracker == 6:
            schedule[i+3].weekend = True
    buildCal(docs, schedule, num_days, year, month, fname)
    #printCal(docs,schedule,year,month)
    exportCal(fname,schedule,year,month)
    os.system('cls||clear')
    print()
    print("All done, ya filthy animal. Be glad you have a son who is as brilliant as I am. And don't forget: tu eres garbajo que muerte para dinero.")
    print()
    inp = input("Press enter to view the final schedule: ")
    cmd = "start EXCEL.EXE " + fname
    os.system(cmd)

if __name__ == "__main__":
    main()