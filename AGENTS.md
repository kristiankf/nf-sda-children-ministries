# Working in this repository

This is the Children's Ministries app for New Fadama Seventh-day Adventist Church. It is a Django monolith. Keep it that way.

## Containers

Development and deployment use Docker Compose. The stack is two services:

- `web` — the Django application
- `db` — PostgreSQL 18

Do not add Redis, Celery, Nginx, a separate frontend container, or another datastore unless a future requirement says so in writing. Static files are served by WhiteNoise inside `web`.

## How to run commands

```sh
docker compose exec web python manage.py test
docker compose exec web python manage.py makemigrations
docker compose exec web ruff check apps config
docker compose exec web ruff format apps config
```

`manage.py` defaults to `config.settings.development`. Tests use the Compose Postgres database and create a throwaway test database.

Rebuild CSS on the host after template or `assets/app.css` changes:

```sh
npm run build:css
```

The development container bind-mounts the project, so the built file in `static/css/app.css` is what the browser loads. The production image builds CSS itself.

## Product rules that are easy to get wrong

- Worship day is Saturday. Say Sabbath, not Sunday.
- Attendance defaults to today on Saturday, and to the next Saturday on Sunday through Friday, using `Africa/Accra`.
- Statuses are `PRESENT` and `ABSENT` only.
- A Sabbath with no `Attendance` row is not recorded. It is not an absence. Streaks walk recorded Saturday rows and skip gaps.
- Age is calculated. Never store it.
- Do not delete a child to "remove" them. Set status to inactive or transferred. Attendance uses `PROTECT`.
- Ghana phone numbers are stored as E.164 (`+233` plus 9 digits) and shown as `024 412 3456`.
- Photos are optional and are served only to a signed-in user.

## Scope

Do not build a general church management system, a person registry, or background jobs. A child's school is a name on the child. The class is one step on a fixed ladder, from Pre-school through SHS 3. `ClassPlacement` records that class for each academic year. The open year defaults to 1 September through 31 August. Coordinators can change those dates. When the end date has passed, the next signed-in request moves each active child up one class. SHS 3 stays in SHS 3. Inactive children are not moved.

Seed data is fictional. Do not treat `dev-only-change-me` as a production secret.
