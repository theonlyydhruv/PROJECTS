from modules.data_manager import load_offerings, save_preferences
from modules.models import Student
from modules.scheduler import Scheduler
from modules.ui import (
    ask_course_codes,
    collect_preferences,
    display_schedule,
    show_filter_history,
    post_schedule_menu,
)

def main():
    print("=" * 78)
    print("                         FFCSOLVER")
    print("            Preference-Based FFCS Timetable Planner")
    print("=" * 78)

    try:
        courses = load_offerings("data/offerings.txt")
    except FileNotFoundError as error:
        print(error)
        return

    if len(courses) == 0:
        print("No course data was found.")
        return

    print("\nAvailable courses in the local data:")
    for code in courses:
        print("{} - {}".format(code, courses[code].name))

    course_codes = ask_course_codes(courses)

    student = Student(course_codes)

    preferences = collect_preferences()

    student.set_preferences(
        preferences[0],
        preferences[1],
        preferences[2],
        preferences[3],
        preferences[4],
    )

    try:
        save_preferences("preferences.txt", student)
    except OSError:
        print("Warning: preferences could not be saved.")

    scheduler = Scheduler(courses, student)

    print("\nGenerating possible FFCS combinations...")
    schedules, history = scheduler.solve()

    if len(schedules) == 0:
        print("\nNo timetable could be generated.")
        print("Try changing your preferences or adding more course offerings.")
        return

    show_filter_history(history)

    print("\n{} suitable timetable(s) remain.".format(len(schedules)))

    current_schedule = schedules[0]

    display_schedule(
        current_schedule,
        scheduler,
        "YOUR AUTOMATICALLY GENERATED FFCS TIMETABLE",
    )

    alternatives = schedules[1:]
    if alternatives:
        print("\nThe solver also found {} alternative timetable(s).".format(len(alternatives)))

    post_schedule_menu(current_schedule, scheduler, alternatives)

if __name__ == "__main__":
    main()
