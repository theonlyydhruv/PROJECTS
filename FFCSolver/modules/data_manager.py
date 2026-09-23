from modules.models import Course, Offering


def load_offerings(filename):
    """Read VTOP FFCS offerings from a simple pipe-separated text file."""
    courses = {}
    try:
        file = open(filename, "r")
    except FileNotFoundError:
        raise FileNotFoundError("Could not find the data file: {}".format(filename))

    for raw_line in file:
        line = raw_line.strip()
        if line == "" or line.startswith("#"):
            continue

        parts = line.split("|")
        if len(parts) != 6:
            continue

        code = parts[0].strip().upper()
        name = parts[1].strip()
        teacher = parts[2].strip()
        slot_group = parts[3].strip().upper()
        component = parts[4].strip()
        room = parts[5].strip()

        offering = Offering(code, name, teacher, slot_group, component, room)
        if code not in courses:
            courses[code] = Course(code, name)
        courses[code].add_offering(offering)

    file.close()
    return courses


def save_preferences(filename, student):
    file = open(filename, "w")
    file.write("COURSES=" + ",".join(student.course_codes) + "\n")
    file.write("PERIOD=" + student.preferred_period + "\n")
    file.write("LUNCH=" + ("required" if student.lunch_required else "not_required") + "\n")
    file.write("FREE_DAY=" + student.free_day + "\n")
    file.write("AVOID_EVENING=" + str(student.avoid_evening) + "\n")
    file.write("MAX_DAYS=" + str(student.max_days) + "\n")
    file.write("VENUE_RULE=AB01_AB02_TRAVEL\n")
    file.close()
