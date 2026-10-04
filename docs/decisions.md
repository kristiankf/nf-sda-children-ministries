# Decisions

## Django templates and HTMX

The people using this app need a phone-friendly site for Sabbath morning, not a separate client. Server-rendered pages keep permission checks and validation in one place. HTMX refreshes search results. The attendance roll filter is a few lines of JavaScript because hiding a row must not drop that child from the POST.

## HTMX 2.0.11

HTMX 2.0.11 is the version vendored in `static/js/htmx.min.js`. It matches the 2.x behavior the templates were written for.

## PostgreSQL

A partial unique constraint for the current academic year is a Postgres feature. Tests run on Postgres for that reason. SQLite is not a supported database.

## Two containers

Compose is how the app is developed and how it is deployed. One container runs Django. One runs PostgreSQL 18.4. Extra infrastructure would add operation work for a single-ministry site.

## WhiteNoise instead of Nginx

Gunicorn does not serve static files. WhiteNoise does that inside the Django container, which keeps the production compose file to the same two services. A TLS proxy, if needed, stays on the host.

## Sabbath and two statuses

The congregation worships on Saturday. The roll's default date is the Saturday of the current or coming week in Accra. A date after today can be opened, and it cannot be saved until that day. Only present and absent are recorded. Excused, late, and partial were dropped so the Sabbath screen stays a single choice.

## Unrecorded is not absent

Taking attendance is a deliberate act. If a Sabbath was never opened, the children were not marked absent. Streaks therefore walk existing Saturday rows. A gap does not increment and does not reset the count. The dashboard uses that streak, and it only highlights two weeks or more.

## Age is calculated

Storing an age would make it wrong on the child's birthday. February 29 is observed on February 28 when the year is not a leap year.

## No person model

Children, parents, and login users are different records. A universal person table would be a guess about a future membership system.

## Class moves with the academic year

The class ladder is fixed, from Pre-school through SHS 3. The school is a name on the child. `ClassPlacement` keeps the class for each academic year. The open year defaults to 1 September through 31 August, and a coordinator can change those dates. When the end date has passed, the next signed-in request moves each active child up one class. SHS 3 does not move on. That check is a query on the request, in the same way birthday and missing-church lists are queries.

## Reminders are queries

Birthdays and missing-church names are dashboard queries. They do not need a worker, a queue, or a scheduler.

## Development passwords

`dev-only-change-me` is a local convenience. Production settings reject it as `SECRET_KEY`, and the seed command will not run with `DEBUG` off.
