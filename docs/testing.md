# Testing

Tests are Django `TestCase` classes next to the apps. They run against PostgreSQL in Compose, which is required for the case-insensitive unique constraints.

```sh
docker compose exec web python manage.py test
```

Use explicit dates. Patch `apps.core.dates.local_today` when a view reads "today". Do not depend on the clock of the machine running the suite.

## What is covered

| Area | Where |
| --- | --- |
| Sabbath default for Monday, Tuesday, Friday, Saturday, Sunday | `apps/attendance/tests/test_calendar.py` |
| Month boundary, year boundary, leap day | same |
| Accra time zone | same |
| Present breaks a streak; missing rows are not absences; future and non-Saturday rows are ignored | `apps/attendance/tests/test_streaks.py` |
| Roll opens on the current Sabbath; non-Saturday warning; next Sabbath not open; teacher saves current only; past summary + CSV; coordinator edits past; duplicate child/date rejected; anonymous redirected | `apps/attendance/tests/test_views.py` |
| Dashboard names a child and the week count | same |
| Create and update a child, optional parent on create (new or link), unique name plus birthday, optional date of birth, Incomplete label when birthday and/or parent is missing, school/address typeahead suggestions, class placement, future date of birth, search by name, phone, and school, photo type | `apps/children/tests/test_children.py` |
| Age, leap-day birthday, month filter | `apps/children/tests/test_birthdays.py` |
| Phone normalization, unique primary phone, two children for one parent, two guardians for one child, link several children from a parent page | `apps/parents/tests/test_parents.py` |
| September–August year, automatic class move, SHS 3 stays, inactive children stay, missed years, year date edits | `apps/schools/tests/test_calendar.py` |
| Groups, login, logout, teacher can edit academic year, only admin is staff | `apps/accounts/tests.py` |
| Add visitor and visit, companion parent, returning visitor, present totals include visitors, follow-up after three visits, convert to child | `apps/visitors/tests/test_visitors.py` |

Factories are in `apps/core/testing.py`.

A 403 in the test output is expected when a test checks that a teacher or anonymous user is denied. The suite is successful when the summary says `OK`.
