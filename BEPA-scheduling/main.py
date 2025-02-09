from utils import *
from scheduler import *
from models import *
import sys
from calendar import monthrange
import os

def main():

    # inp1 = input("Tu eres garbajo que muerte para dinero. Type 'yes' to agree with this statement: ")
    # while inp1.lower().strip() != "yes":
    #     print()
    #     print("You absolute nincompoop. Can't you follow one simple instruction? Let's try again.")
    #     inp1 = input("Tu eres garbajo que muerte para dinero. Type 'yes' to agree with this statement: ")
    # print()
    # inp1 = input("Glad you agree. Now that that's settled, let's get to scheduling. Press enter to continue: ")
    # os.system('cls||clear')

    filepath = sys.argv[1] #path to Excel file
    month, year = load_month_and_year(filepath) #load in month and year as ints
    
    doctors = load_doctor_inputs(filepath) #load in doctor inputs (Name, Doc Type, Min / Max Shifts, Shift Prefs, Flip Shifts)
    load_shifts_requested_off(filepath, doctors, month, year)
    load_previous_month_shifts(filepath, doctors, month, year)
    #print_doctor_info(doctors)

    num_days = monthrange(year, month)[1]
    calendar = [CalDay(date(year, month, day)) for day in range(1, num_days+1)]
    scheduler = Scheduler(doctors, calendar)
    scheduler.initialize_consecutive_shifts_from_previous_month()
    scheduler.schedule_pat()
    scheduler.schedule_remaining_shift4()

    write_scheduled_shifts(filepath, calendar, month, year)
    clear_scheduled_shifts(filepath)

    # Load manually adjusted 4-shifts from Excel before scheduling
    inp = input("When you're done setting the night shifts, save and close out of the Excel document. Press enter when you are ready to continue, you abominable nincompoop: ")
    read_manual_shift4_assignments(filepath, calendar, doctors, month, year,scheduler)
    print_calendar(calendar)
    #debug_print_doctor_shifts(doctors)

    # Ask user how many shifts they want to schedule per day
    while True:
        try:
            num_shifts = int(input("How many shifts should be scheduled per day? (Enter 3 or 4): "))
            if num_shifts in [3, 4]:
                break
            else:
                os.system('cls||clear')
                print("Honestly Geoff, how could you screw this up? Enter 3 or 4. It's not that hard.")
                print()
        except ValueError:
            os.system('cls||clear')
            print("Honestly Geoff, how could you screw this up? Enter 3 or 4. It's not that hard.")
            print()

    # Initialize scheduler and schedule shifts
    scheduler = Scheduler(doctors, calendar)
    scheduler.initialize_consecutive_shifts_from_previous_month()
    scheduler.schedule_remaining_shifts(num_shifts)
    print_calendar(calendar)

    print()
    print("All done, ya filthy animal. Be glad you have a son who is as brilliant as I am. And don't forget: tu eres garbajo que muerte para dinero.")
    print()
    inp = input("Press enter to view the final schedule: ")
    write_scheduled_shifts(filepath, calendar, month, year)

    # os.system('cls||clear')
    # cmd = "start EXCEL.EXE " + filepath
    # os.system(cmd)

if __name__ == "__main__":
    main()