# Data model

Ages are not stored. When a date of birth is known, age is that date compared with today's date in `Africa/Accra`. February 29 is observed on February 28 in a non-leap year, including for age. A missing date of birth means age and birthday-based Sabbath class are unknown until one is saved.

## Entities

```text
AcademicYear 1──* ClassPlacement *──1 Child
Child *──1 AgeGroup   optional Sabbath-class override
Child *──* Parent   through ChildGuardian
Child 1──* Attendance
Visitor 1──* Visit
Visitor 0‥1──0‥1 Child   after convert
Visit *──0‥1 Parent | Child | free-text companion
```

Attendance and guardian foreign keys use `PROTECT`. Deleting a child or parent that is still referenced is rejected. Retiring a child means setting `Child.status` to `INACTIVE` or `TRANSFERRED`. A class placement is removed when its child is removed. Academic years that still have placements cannot be deleted.

### AcademicYear

`name` is the start year and end year, such as `2026/2027`. `end_date` must be on or after `start_date`. At most one row may have `is_current=True`. A new year defaults to 1 September through 31 August. Teachers and coordinators change those dates on the Classes screen.

The day after `end_date`, the next signed-in request opens the following year and moves each active child up one class. There is no separate scheduler. A child in SHS 3 stays in SHS 3. Inactive and transferred children stay where they are. A child with no class is left unplaced.

### Class

The class ladder is fixed:

| Order | Class |
| --- | --- |
| 1 | Pre-school |
| 2 | Nursery 1 |
| 3 | Nursery 2 |
| 4 | KG 1 |
| 5 | KG 2 |
| 6–11 | Basic 1 through Basic 6 |
| 12–14 | JHS 1 through JHS 3 |
| 15–17 | SHS 1 through SHS 3 |

`Child.class_level` is the child's class now. A child already in Pre-school stays in Pre-school. The next class after Pre-school is Nursery 1. `Child.school_name` is the school they attend, stored on the child. The school is not its own table.

`ClassPlacement` stores the class for one child and one academic year. The open year is updated when the child's class is saved. A closed year is left as it was when the next year opened.

### Child

Required fields are first name, last name, gender (`FEMALE`, `MALE`, `UNSPECIFIED`), and status (`ACTIVE`, `INACTIVE`, `TRANSFERRED`). First name, last name, and date of birth together are unique (names compared case-insensitively; middle name is ignored). Two children may share a name when their birthdays differ. Date of birth is optional and may be left blank when unknown; more than one child may have the same name with an unknown birthday. A future date is rejected. Also optional: phone number stored as E.164, school name, class, address, notes, and photo (JPEG, PNG, or WebP, at most 5 MB, stored under a generated filename). School and address stay free text; the form suggests distinct values already used on other children while typing. The list and detail screens mark a child Incomplete when the birthday is missing or no parent/guardian is linked, naming what is missing (birthday, parent, or both). On Add child, a teacher or coordinator may optionally link an existing parent or enter first name, last name, and phone in a modal after the Class section.

### Sabbath class and youth group

`AgeGroup` stores each Sabbath class and youth group: name, inclusive ages, and a color. Teachers and coordinators edit, add, and remove them from More. A child's Sabbath class and youth group are calculated from the date of birth with the same age rules as the rest of the app. They are not stored, except for an optional `sabbath_class_override` when a teacher or coordinator places the child in a different Sabbath class. The youth group always follows the birthday. The table below is the starting set.

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

A parent has a required primary phone and an optional secondary phone, stored as E.164 (`+233` plus 9 digits) and shown as `024 412 3456`. Primary phone is unique. The link stores a relationship: Father, Mother, Guardian, or Other. A parent may be linked to many children, and a child may have many parents. The pair `(child, parent)` is unique. Teachers and coordinators can add the link from the child (one guardian at a time) or from the parent (one or more children in one save, same relationship).

### Attendance

One row per child per date. Status is `PRESENT` or `ABSENT`. `recorded_by` is the user who last saved the row. There is no excused, late, or partial status, and no notes field.

## Sabbath calendar

Saturday is weekday 5 in Python (`date.weekday()`). The **current Sabbath** for recording is:

- today, when today is Saturday
- otherwise the previous Saturday

It stays current until the next Saturday arrives. The clock is `Africa/Accra` via `timezone.localdate()`, not the server's default zone.

The attendance page only keeps Saturdays. A non-Saturday date shows a warning and no roll. The next Saturday (after the current one) shows as not open yet. Past Sabbaths show stats, children present, visitors, and a CSV download. Teachers view past Sabbaths; coordinators and admins can open Edit to use the full roll and save.

## Missing church

`consecutive_absence_weeks` walks a child's attendance rows that fall on a Saturday on or before the cutoff, newest first.

- `ABSENT` adds one week.
- `PRESENT` stops the streak.
- A Saturday with no row is skipped. It neither adds a week nor breaks the streak.
- A row dated after the cutoff is ignored. The cutoff is the latest Saturday on or before today, so a future Saturday does not count yet.
- Non-Saturday dates are rejected on the attendance page, so streak walks stay on Saturdays.

The dashboard card lists children at 2 or more weeks, five names at most. The full Missing church page lists 1 week and above.

If the latest Sabbath has no rows at all, nobody is treated as absent for that week.

## Birthdays

"This week" is today through the next six days. "This month" is the calendar month, including days already passed. Upcoming lists use the observed birthday.

### Visitor and Visit

Visitors are not children and do not appear on the class attendance roll. A `Visitor` stores first name, last name, gender, optional date of birth, and optional address. A `Visit` is one Sabbath appearance: date, reason, and who they came with (an existing parent, an existing child, or an optional free-text name and phone). One visit per visitor per date.

Present totals for a Sabbath add the visit count to children marked PRESENT. Absent and unmarked stay children-only.

After three visits since the last checkup (`follow_up_baseline`), the visitor appears on the home page follow-up list. Marking checked up sets the baseline to the current visit count. After three more visits they appear again. Converting a visitor creates an incomplete `Child` (same name, gender, birthday, address), links `Visitor.child`, and keeps the visit history. Converted visitors leave the follow-up list.

## Not built yet

**A shared Person model.** Children, parents, and users are separate. A later person record could link them. Nothing in the current schema depends on that.
