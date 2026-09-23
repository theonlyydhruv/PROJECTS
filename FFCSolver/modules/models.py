class Offering:
    """One available FFCS offering. A VTOP offering can contain many weekly slots."""

    def __init__(self, course_code, course_name, teacher, slot_group, component="LT", room=""):
        self.course_code = course_code
        self.course_name = course_name
        self.teacher = teacher
        self.slot = slot_group
        self.component = component
        self.room = room

    def slot_codes(self):
        return self.slot.split("+")

    def sessions(self):
        from modules.slot_data import slot_details
        result = []
        for code in self.slot_codes():
            details = slot_details(code)
            if details is not None:
                result.append((code, details[0], details[1], details[2]))
        return result

    def get_day(self):
        sessions = self.sessions()
        return sessions[0][1] if sessions else "Unknown"

    def get_start(self):
        sessions = self.sessions()
        return sessions[0][2] if sessions else "Unknown"

    def get_end(self):
        sessions = self.sessions()
        return sessions[0][3] if sessions else "Unknown"

    def short_text(self):
        return "{} | {} | {} | {} | {}".format(
            self.course_code, self.course_name, self.teacher, self.slot, self.room
        )


class Course:
    """Course containing its available VTOP offerings."""

    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.offerings = []

    def add_offering(self, offering):
        self.offerings.append(offering)

    def teacher_list(self):
        teachers = []
        for offering in self.offerings:
            if offering.teacher not in teachers:
                teachers.append(offering.teacher)
        return teachers


class Person:
    """Base class used to demonstrate inheritance."""

    def __init__(self, name):
        self.name = name


class Student(Person):
    """Stores the student's scheduling preferences."""

    def __init__(self, course_codes, name="Student"):
        super().__init__(name)
        self.course_codes = course_codes
        self.preferred_period = "none"
        # Lunch is optional and is chosen by the user during preference setup.
        self.lunch_required = False
        self.free_day = "none"
        self.avoid_evening = False
        self.max_days = 6

    def set_preferences(self, preferred_period, free_day, avoid_evening, max_days, lunch_required=False):
        self.preferred_period = preferred_period
        self.free_day = free_day
        self.avoid_evening = avoid_evening
        self.max_days = max_days
        self.lunch_required = lunch_required

    def preference_summary(self):
        return "{} | {} | lunch={} | free={} | max_days={}".format(
            self.preferred_period,
            "avoid evening" if self.avoid_evening else "evening allowed",
            "required" if self.lunch_required else "not required",
            self.free_day,
            self.max_days,
        )


class Schedule:
    """A collection of offerings, one for each required course."""

    def __init__(self, offerings):
        self.offerings = offerings

    def course_codes(self):
        return [offering.course_code for offering in self.offerings]

    def teachers(self):
        return [offering.teacher for offering in self.offerings]

    def __len__(self):
        return len(self.offerings)

    def __str__(self):
        return "Schedule({})".format(", ".join(self.course_codes()))
