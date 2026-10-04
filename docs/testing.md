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
| Roll opens on the coming Sabbath; teacher can save; duplicate child/date is rejected; anonymous users are redirected | `apps/attendance/tests/test_views.py` |
| Dashboard names a child and the week count | same |
| Create and update a child, class placement, future date of birth, search by name, phone, and school, teacher forbidden, photo type | `apps/children/tests/test_children.py` |
| Age, leap-day birthday, month filter | `apps/children/tests/test_birthdays.py` |
| Phone normalization, two children for one parent, two guardians for one child | `apps/parents/tests/test_parents.py` |
| September–August year, automatic class move, SHS 3 stays, inactive children stay, missed years, coordinator edits dates | `apps/schools/tests/test_calendar.py` |
| Groups, login, logout, teacher blocked from editing the academic year | `apps/accounts/tests.py` |

Factories are in `apps/core/testing.py`.

A 403 in the test output is expected when a test checks that a teacher or anonymous user is denied. The suite is successful when the summary says `OK`.
