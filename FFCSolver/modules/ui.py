from modules.slot_data import DAY_ORDER


def line():
    print("-" * 110)


def ask_number(prompt, minimum, maximum):
    while True:
        try:
            value = int(input(prompt).strip())
            if minimum <= value <= maximum:
                return value
            print("Enter a number from {} to {}.".format(minimum, maximum))
        except ValueError:
            print("Please enter a valid number.")


def ask_yes_no(prompt):
    while True:
        value = input(prompt).strip().lower()
        if value in ("y", "yes", "1"):
            return True
        if value in ("n", "no", "2"):
            return False
        print("Enter yes/no.")


def ask_course_codes(courses):
    while True:
        text = input("\nEnter required course codes separated by spaces:\n> ").strip().upper()
        codes = text.split()
        if not codes:
            print("Please enter at least one course code.")
            continue

        unknown = [code for code in codes if code not in courses]
        if unknown:
            print("\nThese course codes are not in the VTOP data:")
            print(", ".join(unknown))
            print("Currently loaded: {}".format(", ".join(courses.keys())))
            continue

        unique_codes = []
        for code in codes:
            if code not in unique_codes:
                unique_codes.append(code)
        return unique_codes


def collect_preferences():
    print("\n" + "=" * 90)
    print("PREFERENCE SETUP")
    print("The solver first creates a timetable from your preferences, then lets you change teachers.")
    print("Lunch is optional. If you choose Yes, the lunch session is kept completely free.")
    print("Venue travel is automatically optimized for AB01 and AB02.")
    print("=" * 90)

    print("\n1. Preferred class timing")
    print("   1. Morning")
    print("   2. Afternoon")
    print("   3. Evening")
    print("   4. No preference")
    choice = ask_number("> ", 1, 4)
    periods = {1: "morning", 2: "afternoon", 3: "evening", 4: "none"}
    preferred_period = periods[choice]

    print("\n2. Do you want a lunch break?")
    lunch_required = ask_yes_no("Enter yes/no: ")

    print("\n3. Do you want a completely free day?")
    want_free_day = ask_yes_no("Enter yes/no: ")
    free_day = "none"
    if want_free_day:
        print("\nChoose the day you want free:")
        for index, day in enumerate(DAY_ORDER, 1):
            print("{}. {}".format(index, day))
        free_day = DAY_ORDER[ask_number("> ", 1, len(DAY_ORDER)) - 1]

    print("\n4. Avoid evening classes (18:00–19:30)?")
    avoid_evening = ask_yes_no("Enter yes/no: ")

    print("\n5. Maximum number of college days?")
    max_days = ask_number("Enter 1-6: ", 1, 6)

    # Gap preference was intentionally removed. The solver handles the natural
    # 5-minute FFCS gap and venue movement automatically.
    return (
        preferred_period,
        free_day,
        avoid_evening,
        max_days,
        lunch_required,
    )


def display_schedule(schedule, scheduler, title="FFCS TIMETABLE"):
    print("\n" + "=" * 110)
    print(title)
    print("=" * 110)

    by_day = {}
    for _, day, start, end, offering in scheduler.session_records(schedule):
        if day not in by_day:
            by_day[day] = []
        by_day[day].append((scheduler.minutes(start), start, end, offering))

    for day in DAY_ORDER:
        print("\n{}".format(day.upper()))
        line()
        rows = sorted(by_day.get(day, []), key=lambda row: row[0])

        if not rows:
            print("FREE DAY")
            continue

        # Show the lunch marker only when the student requested a lunch break.
        inserted_lunch = False
        for _, start, end, offering in rows:
            if (scheduler.student.lunch_required and not inserted_lunch
                    and scheduler.minutes(start) >= scheduler.minutes("14:50")):
                print("                 | {:6} | {:10} | {:28} | {:8} | {:8}".format(
                    scheduler.LUNCH_SLOTS[day], "LUNCH", "Lunch Break", "", ""
                ))
                inserted_lunch = True

            slot_code = next(
                (x[0] for x in offering.sessions() if x[2] == start and x[3] == end),
                offering.slot,
            )
            building = scheduler.venue_group(offering.room)
            print(
                "{} - {} | {:6} | {:10} | {:28} | {:8} | {:8}".format(
                    start, end, slot_code, offering.course_code,
                    offering.teacher[:28], building, offering.room,
                )
            )

        if scheduler.student.lunch_required and not inserted_lunch:
            print("                 | {:6} | {:10} | {:28} | {:8} | {:8}".format(
                scheduler.LUNCH_SLOTS[day], "LUNCH", "Lunch Break", "", ""
            ))

        # Show a travel note only when the day actually requires a building change.
        day_travel = []
        for day_name, gap, from_building, to_building, old_offering, new_offering in scheduler.transition_details(schedule)["switches"]:
            if day_name == day:
                day_travel.append((gap, from_building, to_building))
        for gap, from_building, to_building in day_travel:
            print("  Travel: {} → {} | {} minute gap".format(
                from_building, to_building, gap
            ))

    line()
    days = scheduler.days_used(schedule)
    details = scheduler.transition_details(schedule)
    print("College days        : {}".format(len(days)))
    print("Days used           : {}".format(", ".join(day for day in DAY_ORDER if day in days)))
    print("Lunch               : {}".format("Protected" if scheduler.student.lunch_required else "Not required"))
    print("Venue layout penalty : {}".format(scheduler.venue_layout_penalty(schedule)))
    print("Venue switches       : {}".format(len(details["switches"])))
    print("AB01↔AB02 quick days : {} / {}".format(len(details["quick_days"]), scheduler.MAX_QUICK_TRAVEL_DAYS))
    print("Evening class       : {}".format("Yes" if scheduler.has_evening_class(schedule) else "No"))

def show_filter_history(history):
    print("\n" + "=" * 90)
    print("SOLVER PROCESS")
    print("=" * 90)
    for name, count in history:
        print("{:<52} {}".format(name, count))


def change_teacher_menu(current_schedule, scheduler):
    print("\n" + "=" * 90)
    print("CHANGE TEACHER")
    print("=" * 90)

    for index, offering in enumerate(current_schedule.offerings, 1):
        print("{}. {} - {} - {} - {}".format(
            index, offering.course_code, offering.course_name, offering.teacher, offering.room
        ))
    print("0. Back")

    choice = ask_number("> ", 0, len(current_schedule.offerings))
    if choice == 0:
        return current_schedule

    selected = current_schedule.offerings[choice - 1]
    course = scheduler.courses[selected.course_code]
    teachers = course.teacher_list()

    print("\nAvailable teachers for {}:".format(selected.course_code))
    for index, teacher in enumerate(teachers, 1):
        print("{}. {}".format(index, teacher))

    teacher_choice = ask_number("> ", 1, len(teachers))
    new_teacher = teachers[teacher_choice - 1]
    if new_teacher == selected.teacher:
        print("That teacher is already selected.")
        return current_schedule

    candidates, error = scheduler.change_teacher(current_schedule, selected.course_code, new_teacher)
    if error:
        print("\n" + error)
        return current_schedule

    print("\nTeacher changed. The solver checked conflicts, the selected lunch preference and venue travel, then rebuilt the timetable.")
    updated = candidates[0]
    display_schedule(updated, scheduler, "UPDATED FFCS TIMETABLE")
    return updated


def post_schedule_menu(schedule, scheduler, alternatives=None):
    alternatives = alternatives or []
    current_index = 0

    while True:
        print("\n" + "=" * 90)
        print("WHAT WOULD YOU LIKE TO DO?")
        print("=" * 90)
        print("1. Change teacher")
        print("2. View next suitable timetable")
        print("3. View current timetable")
        print("4. Exit")

        choice = ask_number("> ", 1, 4)

        if choice == 1:
            schedule = change_teacher_menu(schedule, scheduler)

        elif choice == 2:
            if not alternatives:
                print("\nNo additional timetable was generated.")
            else:
                current_index += 1
                if current_index >= len(alternatives):
                    current_index = 0
                schedule = alternatives[current_index]
                display_schedule(schedule, scheduler, "ALTERNATIVE FFCS TIMETABLE")

        elif choice == 3:
            display_schedule(schedule, scheduler, "CURRENT FFCS TIMETABLE")

        else:
            print("\nThank you for using FFCSolver.")
            break

    return schedule
