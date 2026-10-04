# Data model

Ages are not stored. A child's age is `date of birth` compared with today's date in `Africa/Accra`. February 29 is observed on February 28 in a non-leap year, including for age.

## Entities

```text
AcademicYear 1──* ClassPlacement *──1 Child
Child *──1 AgeGroup   optional Sabbath-class override
Child *──* Parent   through ChildGuardian
Child 1──* Attendance
```

Attendance and guardian foreign keys use `PROTECT`. Deleting a child or parent that is still referenced is rejected. Retiring a child means setting `Child.status` to `INACTIVE` or `TRANSFERRED`. A class placement is removed when its child is removed. Academic years that still have placements cannot be deleted.

### AcademicYear

`name` is the start year and end year, such as `2026/2027`. `end_date` must be on or after `start_date`. At most one row may have `is_current=True`. A new year defaults to 1 September through 31 August. Coordinators change those dates on the Classes screen.

The day after `end_date`, the next signed-in request opens the following year and moves each active child up one class. There is no separate scheduler. A child in SHS 3 stays in SHS 3. Inactive and transferred children stay where they are. A child with no class is left unplaced.

### Class

The class ladder is fixed:

| Order | Class |
| --- | --- |
| 1 | Pre-school |
| 2–7 | Basic 1 through Basic 6 |
| 8–10 | JHS 1 through JHS 3 |
| 11–13 | SHS 1 through SHS 3 |

`Child.class_level` is the child's class now. `Child.school_name` is the school they attend, stored on the child. The school is not its own table.

`ClassPlacement` stores the class for one child and one academic year. The open year is updated when the child's class is saved. A closed year is left as it was when the next year opened.

### Child

Names, date of birth, gender (`FEMALE`, `MALE`, `UNSPECIFIED`), an optional phone number stored as E.164, optional school name, optional class, address, notes, and status (`ACTIVE`, `INACTIVE`, `TRANSFERRED`). A date of birth in the future is rejected. The optional photo is JPEG, PNG, or WebP, at most 5 MB, stored under a generated filename.

### Sabbath class and youth group

`AgeGroup` stores each Sabbath class and youth group: name, inclusive ages, and a color. Coordinators edit, add, and remove them from More. A child's Sabbath class and youth group are calculated from the date of birth with the same age rules as the rest of the app. They are not stored, except for an optional `sabbath_class_override` when a coordinator places the child in a different Sabbath class. The youth group always follows the birthday. The table below is the starting set.

| Sabbath class | Age |
| --- | --- |
| Baby Steps | Under 1 year, until the first birthday |
| Beginner | 1–3 |
| Kindergarten | 4–6 |
| Primary | 7–9 |
| Power Point | 10–12 |
| RealTime | 13–14 |
| Corner Stone | 15 and older |

| Youth group | Age |
| --- | --- |
| Adventurer | 4–9 |
| Pathfinder | 10–15 |

A child younger than 4 or older than 15 has no youth group. Graduating a Corner Stone child sets status to inactive and keeps attendance.

### Parent and ChildGuardian

A parent has a required primary phone and an optional secondary phone, stored as E.164. The link stores a relationship: Father, Mother, Guardian, or Other. A parent may be linked to many children, and a child may have many parents. The pair `(child, parent)` is unique.

### Attendance

One row per child per date. Status is `PRESENT` or `ABSENT`. `recorded_by` is the user who last saved the row. There is no excused, late, or partial status, and no notes field.

## Sabbath calendar

Saturday is weekday 5 in Python (`date.weekday()`). "This Sabbath" on the attendance page is:

- today, when today is Saturday
- otherwise the next Saturday

That rule crosses month ends, year ends, and leap days. The clock is `Africa/Accra` via `timezone.localdate()`, not the server's default zone.

The roll can be opened through that coming Sabbath. A date after today cannot be saved. Saving stays closed until that day in Accra.

## Missing church

`consecutive_absence_weeks` walks a child's attendance rows that fall on a Saturday on or before the cutoff, newest first.

- `ABSENT` adds one week.
- `PRESENT` stops the streak.
- A Saturday with no row is skipped. It neither adds a week nor breaks the streak.
- A row dated after the cutoff is ignored. The cutoff is the latest Saturday on or before today, so a future Saturday does not count yet.
- A non-Saturday row can be stored if someone picks that date, and the roll warns that it will not affect streaks.

The dashboard card lists children at 2 or more weeks, five names at most. The full Missing church page lists 1 week and above.

If the latest Sabbath has no rows at all, nobody is treated as absent for that week.

## Birthdays

"This week" is today through the next six days. "This month" is the calendar month, including days already passed. Upcoming lists use the observed birthday.

## Not built yet

**A shared Person model.** Children, parents, and users are separate. A later person record could link them. Nothing in the current schema depends on that.
