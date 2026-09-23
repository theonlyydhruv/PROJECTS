import itertools
from modules.models import Schedule
from modules.slot_data import DAY_ORDER


class Scheduler:
    """Generates and filters FFCS schedules using VTOP slot groups."""

    # FFCS timing gives only a 5-minute gap between normal successive sessions.
    # Same-building movement is treated as fine. For AB01 <-> AB02, a 5-minute
    # transfer is manageable, but we deliberately allow it on only two days.
    NORMAL_TRAVEL_MINUTES = 10
    AB01_AB02_QUICK_TRAVEL_MINUTES = 5
    MAX_QUICK_TRAVEL_DAYS = 2

    LUNCH_SLOTS = {
        "Monday": "A21",
        "Tuesday": "D21",
        "Wednesday": "A22",
        "Thursday": "D22",
        "Friday": "A23",
        "Saturday": "D23",
    }

    def __init__(self, courses, student):
        self.courses = courses
        self.student = student

    def get_option_lists(self):
        option_lists = []
        for code in self.student.course_codes:
            course = self.courses.get(code)
            if course is None:
                return None, "Course {} is not present in the data.".format(code)
            if len(course.offerings) == 0:
                return None, "Course {} has no offerings.".format(code)

            # Automatic generation uses one representative per unique slot group.
            # Faculty selection is intentionally a second-stage action.
            unique = []
            seen_slots = set()
            for offering in course.offerings:
                if offering.slot not in seen_slots:
                    seen_slots.add(offering.slot)
                    unique.append(offering)
            option_lists.append(unique)
        return option_lists, ""

    def generate_combinations(self):
        option_lists, error = self.get_option_lists()
        if option_lists is None:
            return [], error

        partial = [()]
        for options in option_lists:
            partial = list(itertools.product(partial, options))
            next_partial = []
            for previous, offering in partial:
                selected = list(previous)
                candidate = Schedule(selected + [offering])
                if not self.has_time_conflict(candidate):
                    next_partial.append(tuple(selected + [offering]))
            partial = next_partial
            if not partial:
                break

        return [Schedule(list(item)) for item in partial], ""

    def session_records(self, schedule):
        records = []
        for offering in schedule.offerings:
            for slot_code, day, start, end in offering.sessions():
                records.append((slot_code, day, start, end, offering))
        return records

    def minutes(self, time_text):
        parts = time_text.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    def has_time_conflict(self, schedule):
        used = set()
        for slot_code, day, start, end, offering in self.session_records(schedule):
            key = (day, start, end)
            if key in used:
                return True
            used.add(key)
        return False

    def days_used(self, schedule):
        days = set()
        for _, day, _, _, _ in self.session_records(schedule):
            days.add(day)
        return days

    def day_sessions(self, schedule):
        by_day = {}
        for _, day, start, end, offering in self.session_records(schedule):
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(
                (self.minutes(start), self.minutes(end), start, end, offering)
            )
        for day in by_day:
            by_day[day].sort()
        return by_day

    def venue_group(self, room):
        """Convert room numbers into practical buildings for travel checking."""
        room = (room or "").strip().upper()
        if room.startswith("AB02-"):
            return "AB02"
        if room.startswith("AB-"):
            return "AB01"
        if room.startswith("AB01-"):
            return "AB01"
        if room:
            return room.split("-")[0]
        return "UNKNOWN"

    def lunch_available(self, schedule, day):
        """Return True when the 13:15–14:45 lunch session is completely free."""
        lunch_slot = self.LUNCH_SLOTS[day]
        for slot_code, session_day, _, _, _ in self.session_records(schedule):
            if session_day == day and slot_code == lunch_slot:
                return False
        return True

    def lunch_days(self, schedule):
        return [day for day in DAY_ORDER if self.lunch_available(schedule, day)]

    def has_lunch_break(self, schedule):
        # When the student requests lunch, no selected class may occupy the
        # normal 13:15–14:45 lunch session on any day.
        for day in DAY_ORDER:
            if not self.lunch_available(schedule, day):
                return False
        return True

    def transition_details(self, schedule):
        """Analyse building changes between consecutive classes.

        Same building: no travel penalty.
        Different building with >= 10 minutes: acceptable.
        AB01 <-> AB02 with the normal 5-minute FFCS gap: acceptable, but only
        on up to two days in the week because the buildings are far apart.
        Other 5-minute building changes are rejected.
        """
        switches = []
        quick_days = set()
        invalid = []

        for day, sessions in self.day_sessions(schedule).items():
            for index in range(len(sessions) - 1):
                current = sessions[index]
                following = sessions[index + 1]
                current_end = current[1]
                next_start = following[0]
                gap = next_start - current_end
                current_offering = current[4]
                next_offering = following[4]
                current_building = self.venue_group(current_offering.room)
                next_building = self.venue_group(next_offering.room)

                if current_building == next_building:
                    continue

                switches.append((day, gap, current_building, next_building,
                                 current_offering, next_offering))

                if gap >= self.NORMAL_TRAVEL_MINUTES:
                    continue

                if ({current_building, next_building} == {"AB01", "AB02"}
                        and gap >= self.AB01_AB02_QUICK_TRAVEL_MINUTES):
                    quick_days.add(day)
                else:
                    invalid.append((day, gap, current_building, next_building))

        if len(quick_days) > self.MAX_QUICK_TRAVEL_DAYS:
            return {
                "valid": False,
                "switches": switches,
                "quick_days": quick_days,
                "invalid": invalid + [("WEEK", 5, "AB01", "AB02")],
            }

        return {
            "valid": len(invalid) == 0,
            "switches": switches,
            "quick_days": quick_days,
            "invalid": invalid,
        }

    def venue_travel_valid(self, schedule):
        return self.transition_details(schedule)["valid"]

    def venue_layout_penalty(self, schedule):
        """Prefer one building per part of the day.

        The student's practical pattern is morning in AB01 and afternoon in AB02
        (or the reverse). The solver therefore prefers schedules where the morning
        classes stay together in one building and the afternoon classes stay
        together in one building, instead of bouncing between AB01 and AB02.
        A switch across the lunch break is not treated as a bad 5-minute transfer
        because the lunch period provides ample movement time.
        """
        penalty = 0
        for _, sessions in self.day_sessions(schedule).items():
            morning_buildings = set()
            afternoon_buildings = set()
            for start_minutes, _, _, _, offering in sessions:
                building = self.venue_group(offering.room)
                if start_minutes < self.minutes("13:15"):
                    morning_buildings.add(building)
                elif start_minutes >= self.minutes("14:50"):
                    afternoon_buildings.add(building)

            if len(morning_buildings) > 1:
                penalty += len(morning_buildings) - 1
            if len(afternoon_buildings) > 1:
                penalty += len(afternoon_buildings) - 1

        return penalty

    def venue_switch_count(self, schedule):
        return len(self.transition_details(schedule)["switches"])

    def quick_travel_days(self, schedule):
        return len(self.transition_details(schedule)["quick_days"])

    def max_gap_minutes(self, schedule):
        largest = 0
        for _, sessions in self.day_sessions(schedule).items():
            for index in range(len(sessions) - 1):
                gap = sessions[index + 1][0] - sessions[index][1]
                if gap > largest:
                    largest = gap
        return largest

    def has_evening_class(self, schedule):
        for _, _, start, _, _ in self.session_records(schedule):
            if start == "18:00":
                return True
        return False

    def period_counts(self, schedule):
        counts = {"morning": 0, "afternoon": 0, "evening": 0}
        for _, _, start, _, _ in self.session_records(schedule):
            if start in ("08:30", "10:05"):
                counts["morning"] += 1
            elif start in ("11:40", "13:15", "14:50", "16:25"):
                counts["afternoon"] += 1
            elif start == "18:00":
                counts["evening"] += 1
        return counts

    def matches_period(self, schedule):
        preferred = self.student.preferred_period
        if preferred == "none":
            return True
        counts = self.period_counts(schedule)
        total = sum(counts.values())
        return total == 0 or counts[preferred] * 2 >= total

    def filter_conflicts(self, schedules):
        return [schedule for schedule in schedules if not self.has_time_conflict(schedule)]

    def filter_lunch(self, schedules):
        if not self.student.lunch_required:
            return schedules
        return [schedule for schedule in schedules if self.has_lunch_break(schedule)]

    def filter_travel(self, schedules):
        return [schedule for schedule in schedules if self.venue_travel_valid(schedule)]

    def filter_evening(self, schedules):
        if not self.student.avoid_evening:
            return schedules
        return [schedule for schedule in schedules if not self.has_evening_class(schedule)]

    def filter_period(self, schedules):
        if self.student.preferred_period == "none":
            return schedules
        return [schedule for schedule in schedules if self.matches_period(schedule)]

    def filter_free_day(self, schedules):
        if self.student.free_day == "none":
            return schedules
        return [schedule for schedule in schedules if self.student.free_day not in self.days_used(schedule)]

    def filter_max_days(self, schedules):
        return [schedule for schedule in schedules if len(self.days_used(schedule)) <= self.student.max_days]

    def apply_filter_safely(self, schedules, filter_function, name):
        result = filter_function(schedules)
        if len(result) == 0:
            # Do not destroy all results because of a soft preference. Travel and
            # lunch are project requirements, so callers handle them as hard filters.
            return schedules, False, name
        return result, True, name

    def solve(self):
        schedules, error = self.generate_combinations()
        if error:
            return [], [error]

        history = [("Generated combinations", len(schedules))]

        schedules = self.filter_conflicts(schedules)
        history.append(("Removed time conflicts", len(schedules)))
        if not schedules:
            return [], ["No conflict-free schedule exists for these courses."]

        # Lunch is a user-selected requirement. If the user chooses No,
        # the solver does not filter schedules based on lunch.
        if self.student.lunch_required:
            schedules = self.filter_lunch(schedules)
            history.append(("Required a lunch session", len(schedules)))
            if not schedules:
                return [], ["No schedule leaves a lunch session free."]
        else:
            history.append(("Lunch break not required", len(schedules)))

        schedules = self.filter_travel(schedules)
        history.append(("Applied venue/travel rule", len(schedules)))
        if not schedules:
            return [], [
                "No schedule satisfies the venue travel rule. "
                "The solver allows the 5-minute AB01↔AB02 transfer on at most two days."
            ]

        # Remaining answers are preferences. If one preference would remove every
        # schedule, keep the previous set and continue, rather than failing.
        filters = [
            (self.filter_free_day, "Free-day preference"),
            (self.filter_evening, "Avoid-evening preference"),
            (self.filter_period, "Preferred timing"),
            (self.filter_max_days, "Maximum college days"),
        ]

        for filter_function, name in filters:
            schedules, applied, filter_name = self.apply_filter_safely(
                schedules, filter_function, name
            )
            history.append((filter_name + (" applied" if applied else " could not be applied"), len(schedules)))

        # Prefer fewer building changes, then fewer days, then fewer quick
        # AB01<->AB02 transfers. This is the automatic venue optimization.
        schedules.sort(key=lambda schedule: (
            self.venue_layout_penalty(schedule),
            self.venue_switch_count(schedule),
            self.quick_travel_days(schedule),
            len(self.days_used(schedule)),
            1 if self.has_evening_class(schedule) else 0,
        ))
        return schedules, history

    def change_teacher(self, current_schedule, course_code, new_teacher):
        """Rebuild the timetable after a teacher change.

        The old implementation kept every other course on exactly the same
        offering. That was too restrictive: changing one teacher can require
        another course to move to a different valid slot. We therefore lock the
        requested teacher and regenerate the complete timetable while preserving
        the student's preferences and hard constraints.
        """
        if course_code not in self.courses:
            return [], "Course does not exist."

        course = self.courses[course_code]
        teacher_options = [
            offering for offering in course.offerings
            if offering.teacher == new_teacher
        ]
        if not teacher_options:
            return [], "That teacher has no offering for this course."

        # Build the same search space as the normal solver, but force the
        # selected course to use the requested teacher.
        option_lists = []
        for code in self.student.course_codes:
            current_course = self.courses.get(code)
            if current_course is None or not current_course.offerings:
                return [], "Course {} has no offerings.".format(code)

            if code == course_code:
                options = teacher_options
            else:
                # Keep one offering for each unique slot group. Faculty is
                # allowed to change for other courses if that is necessary to
                # make the new timetable work.
                options = []
                seen_slots = set()
                for offering in current_course.offerings:
                    if offering.slot not in seen_slots:
                        seen_slots.add(offering.slot)
                        options.append(offering)

            option_lists.append(options)

        partial = [()]
        for options in option_lists:
            next_partial = []
            for previous in partial:
                for offering in options:
                    selected = list(previous)
                    selected.append(offering)
                    candidate = Schedule(selected)

                    # Reject as soon as a partial timetable becomes impossible.
                    if self.has_time_conflict(candidate):
                        continue
                    next_partial.append(tuple(selected))
            partial = next_partial
            if not partial:
                break

        candidates = [Schedule(list(item)) for item in partial]

        # Hard constraints first.
        candidates = self.filter_conflicts(candidates)
        if self.student.lunch_required:
            candidates = self.filter_lunch(candidates)
        candidates = self.filter_travel(candidates)

        if not candidates:
            return [], (
                "No timetable was found with {} as the teacher for {} while "
                "keeping the selected hard constraints. The solver did try "
                "moving the other courses to different valid offerings."
            ).format(new_teacher, course_code)

        # Apply the user's soft preferences. If a preference would remove every
        # candidate, keep the previous candidate set and continue.
        filters = [
            self.filter_free_day,
            self.filter_evening,
            self.filter_period,
            self.filter_max_days,
        ]
        for filter_function in filters:
            candidates, _, _ = self.apply_filter_safely(
                candidates, filter_function, "Preference"
            )

        # Prefer practical timetables. Fewer venue changes and fewer college
        # days are better, while preserving the requested teacher.
        candidates.sort(key=lambda schedule: (
            self.venue_layout_penalty(schedule),
            self.venue_switch_count(schedule),
            self.quick_travel_days(schedule),
            len(self.days_used(schedule)),
            1 if self.has_evening_class(schedule) else 0,
        ))

        return candidates, ""
