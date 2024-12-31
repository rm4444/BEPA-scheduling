class Doctor:
    def __init__(self,name,days_off,shift_prefs,min_shifts,max_shifts):
        self.name = name
        self.days_off = days_off
        # self.OneSO = OneSO
        # self.TwoSO = TwoSO
        # self.ThreeSO = ThreeSO
        # self.FourSO = FourSO
        self.shift_prefs = shift_prefs
        self.min_shifts = min_shifts
        self.max_shifts = max_shifts
        self.shifts = 0
        self.weekends = 0
        self.consec_shifts = 0
        self.four_shifts = 0
        self.lastSixDays = 0
        self.lastNineDays = 0

class CalDay:
    def __init__(self,date):
        self.date = date
        self.s1 = Doctor("--",[],[],[],[],[],[],0,0)
        self.s2 = Doctor("--",[],[],[],[],[],[],0,0)
        self.s3 = Doctor("--",[],[],[],[],[],[],0,0)
        self.s4 = Doctor("--",[],[],[],[],[],[],0,0)
        self.weekend = False

class Gap:
    def __init__(self,start_date,length):
        self.start_date = start_date
        self.length = length
        self.remaining = length
        self.filled = False
        self.docs = []