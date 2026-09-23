# FFCSolver

FFCSolver is a Python-based timetable generator made for managing and creating FFCS timetables.

The main idea of this project is to select courses, teachers and preferences and then generate possible timetables while checking things like class clashes, lunch breaks and travel time between buildings.

## What it does

- Select courses for the semester
- Select preferred teachers
- Generate different possible timetables
- Check for class time conflicts
- Optionally keep lunch time free
- Check travel time between different buildings
- Handle quick travel between AB01 and AB02
- Consider preferences like morning classes, avoiding evening classes, free days and maximum college days
- Change the teacher of a course and regenerate the timetable around that teacher

## Important Note About the Data

The course and faculty data included in this project is **testing data**.

I used some sample/testing VTOP-style course offering data while developing and testing the scheduler. The data is mainly used to check whether the timetable generation logic, teacher selection, slot handling and conflict checking are working correctly.

The data in this project should **not** be treated as the complete or current VTOP course offering list.

If the actual VTOP data changes, the `offerings.txt` file can be updated with the required course offerings.

## How the timetable works

A course can have multiple slots in one offering. For example, one course may have slots like:

`A11 + A12 + A13 + A14`

These are part of the same course offering and are not separate course selections.

The solver expands these slots into their actual days and timings and checks them while creating the timetable.

## Teacher Change

When a teacher is changed, the solver locks the selected teacher and generates the timetable again. This allows other courses to move to different valid slots if required.

## Project Structure

```text
FFCSolver/
│
├── main.py
├── preferences.txt
├── README.md
│
├── data/
│   └── offerings.txt
│
├── modules/
│   ├── models.py
│   ├── scheduler.py
│   ├── data_manager.py
│   ├── slot_data.py
│   └── ui.py
│
└── test_scheduler.py
```

## Requirements

- Python 3.x

The project mainly uses Python's standard libraries, so there is no complicated setup required.

## Running the Project

Open the project folder in a terminal and run:

```bash
python main.py
```

Follow the options shown in the terminal to select courses, preferences and generate timetables.

## Testing

The project also includes `test_scheduler.py` for testing some of the scheduler functions.

Run it using:

```bash
python test_scheduler.py
```

The testing was done using the sample/testing course data included with the project.

## Limitations

This is a project version and not a complete replacement for the official VTOP FFCS system.

Some limitations are:

- The included course data is only testing/sample data.
- Actual VTOP offerings can change.
- Teacher availability and slot information may be different in the actual FFCS registration period.
- The generated timetable should be checked against the actual VTOP timetable before using it for registration.

## Purpose

This project was mainly made to experiment with timetable generation and scheduling logic for FFCS.

The focus was on making the process of trying different course, teacher and timetable combinations easier instead of manually checking every possible combination.

---

Made as a student project for learning and experimenting with Python, scheduling logic and FFCS timetable generation.
