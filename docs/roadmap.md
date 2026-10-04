# Roadmap

The current app covers children's records, guardians, classes, Sabbath attendance, birthdays, and simple CSV reports for New Fadama Seventh-day Adventist Church.

These items are not scheduled. They are recorded so they are not built by accident.

## Person record

If the same human must be a parent and a login user, or a child who later becomes a teacher, introduce a person record and link the existing tables to it. Do not merge the tables until that need is real.

## Email reminders

The dashboard already lists birthdays and children missing church. Sending those lists by email can use Django's email backend on a manual action or a system cron that calls a management command. That still does not require Celery or Redis.

## Anything else

A new container, cache, or queue needs a requirement that the two-container app cannot meet. Until then, leave Compose as Django plus PostgreSQL.
