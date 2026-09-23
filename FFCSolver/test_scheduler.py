from modules.data_manager import load_offerings
from modules.models import Student, Schedule
from modules.scheduler import Scheduler

courses = load_offerings("data/offerings.txt")
assert set(courses.keys()) == {"MAT1003", "CHY1006", "ENG1004", "CSE1021"}

student = Student(["MAT1003", "CHY1006", "ENG1004", "CSE1021"])
student.set_preferences("none", "none", False, 6, True)
scheduler = Scheduler(courses, student)

schedules, history = scheduler.solve()
assert len(schedules) > 0
assert len(schedules[0].offerings) == 4

# Two offerings sharing A11 must conflict even when their slot-group strings differ.
a = courses["MAT1003"].offerings[0]
b = courses["ENG1004"].offerings[0]
assert scheduler.has_time_conflict(Schedule([a, b])) is True

# When lunch is requested, every day must keep the 13:15 lunch session free.
assert student.lunch_required is True
assert scheduler.has_lunch_break(schedules[0]) is True
for day, slot in scheduler.LUNCH_SLOTS.items():
    assert scheduler.lunch_available(schedules[0], day) is True

# Every returned schedule satisfies the automatic venue-travel rule.
assert scheduler.venue_travel_valid(schedules[0]) is True

# There is no user-facing maximum-gap preference anymore.
assert not hasattr(student, "max_gap")

# Lunch can be disabled by the user; then it must not filter schedules.
student_no_lunch = Student(["MAT1003", "CHY1006", "ENG1004", "CSE1021"])
student_no_lunch.set_preferences("none", "none", False, 6, False)
scheduler_no_lunch = Scheduler(courses, student_no_lunch)
no_lunch_schedules, _ = scheduler_no_lunch.solve()
assert len(no_lunch_schedules) > 0

print("FFCSolver tests passed.")
