# Weekly FFCS slot information.
# Based on the timetable supplied for the project.

SLOT_INFO = {
    "A11": ("Monday", "08:30", "10:00"),
    "B11": ("Monday", "10:05", "11:35"),
    "C11": ("Monday", "11:40", "13:10"),
    "A21": ("Monday", "13:15", "14:45"),
    "A14": ("Monday", "14:50", "16:20"),
    "B21": ("Monday", "16:25", "17:55"),
    "C21": ("Monday", "18:00", "19:30"),

    "D11": ("Tuesday", "08:30", "10:00"),
    "E11": ("Tuesday", "10:05", "11:35"),
    "F11": ("Tuesday", "11:40", "13:10"),
    "D21": ("Tuesday", "13:15", "14:45"),
    "E14": ("Tuesday", "14:50", "16:20"),
    "E21": ("Tuesday", "16:25", "17:55"),
    "F21": ("Tuesday", "18:00", "19:30"),

    "A12": ("Wednesday", "08:30", "10:00"),
    "B12": ("Wednesday", "10:05", "11:35"),
    "C12": ("Wednesday", "11:40", "13:10"),
    "A22": ("Wednesday", "13:15", "14:45"),
    "B14": ("Wednesday", "14:50", "16:20"),
    "B22": ("Wednesday", "16:25", "17:55"),
    "A24": ("Wednesday", "18:00", "19:30"),

    "D12": ("Thursday", "08:30", "10:00"),
    "E12": ("Thursday", "10:05", "11:35"),
    "F12": ("Thursday", "11:40", "13:10"),
    "D22": ("Thursday", "13:15", "14:45"),
    "F14": ("Thursday", "14:50", "16:20"),
    "E22": ("Thursday", "16:25", "17:55"),
    "F22": ("Thursday", "18:00", "19:30"),

    "A13": ("Friday", "08:30", "10:00"),
    "B13": ("Friday", "10:05", "11:35"),
    "C13": ("Friday", "11:40", "13:10"),
    "A23": ("Friday", "13:15", "14:45"),
    "C14": ("Friday", "14:50", "16:20"),
    "B23": ("Friday", "16:25", "17:55"),
    "B24": ("Friday", "18:00", "19:30"),

    "D13": ("Saturday", "08:30", "10:00"),
    "E13": ("Saturday", "10:05", "11:35"),
    "F13": ("Saturday", "11:40", "13:10"),
    "D23": ("Saturday", "13:15", "14:45"),
    "D14": ("Saturday", "14:50", "16:20"),
    "D24": ("Saturday", "16:25", "17:55"),
    "E23": ("Saturday", "18:00", "19:30"),
}

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

TIME_ORDER = {
    "08:30": 0,
    "10:05": 1,
    "11:40": 2,
    "13:15": 3,
    "14:50": 4,
    "16:25": 5,
    "18:00": 6,
}

def slot_details(slot):
    return SLOT_INFO.get(slot)

def is_evening(slot):
    details = slot_details(slot)
    if details is None:
        return False
    return details[1] == "18:00"

def is_morning(slot):
    details = slot_details(slot)
    if details is None:
        return False
    return details[1] in ("08:30", "10:05")

def is_afternoon(slot):
    details = slot_details(slot)
    if details is None:
        return False
    return details[1] in ("11:40", "13:15", "14:50")

def slot_number(slot):
    details = slot_details(slot)
    if details is None:
        return 99
    return TIME_ORDER.get(details[1], 99)
