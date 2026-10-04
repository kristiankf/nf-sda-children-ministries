# Development

`compose.yaml` builds the `development` target, mounts the repository at `/app`, and runs Django's development server on `0.0.0.0:8000`. The entrypoint migrates on every start.

Settings come from `.env` through `config.settings.development`, which forces `DEBUG` on and the console email backend. Messages that would be emailed are printed in `docker compose logs web`.

## Everyday commands

```sh
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test
docker compose exec web ruff check apps config
docker compose exec web ruff format apps config
docker compose logs -f web
```

`exec` does not re-run the entrypoint. `docker compose run --rm web python manage.py test` does, including the wait-for-Postgres and migrate steps.

Ruff is installed only in the development image (`ruff==0.16.10`). It is not in `requirements.txt`. Line length is 100. Rules are E, F, I, UP, and B. Generated migrations may keep long lines.

## Dates in tests

Do not call the real clock for a Sabbath example. Patch `apps.core.dates.local_today` or pass an explicit `date`. Helpers live in `apps/attendance/calendar.py` and `apps/core/dates.py`.

## Roles

`apps.accounts.roles.ensure_ministry_roles` runs after migrations, once the attendance content type exists. It is safe to run more than once.

| Group | Access |
| --- | --- |
| `TEACHER` | View children, parents, classes, and the academic year. Add, change, and delete attendance so a wrong mark can be cleared. |
| `COORDINATOR` | Add, change, and delete ministry records. `is_staff`, so Django admin is available for the models they can manage. |
| `ADMIN` | All permissions. The seeded admin is also a superuser. |

Coordinators edit the open academic year's dates on the Classes screen. User accounts are managed in Django admin.

## UI

The layout is a single column, `max-w-3xl`, with a bottom navigation bar: Home, Children, Attendance, More. Check a phone-width window after layout changes. The attendance save bar sticks under the header so it does not cover the first child's Present and Absent choices.

## Seed data

`seed_dev_data` is sample data for New Fadama screens. Names such as Sample Harbour Basic School are fictional. Re-running the command updates the same rows rather than duplicating them.
