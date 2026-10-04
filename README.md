# New Fadama SDA Children's Ministries

Records and Sabbath attendance for the Children's Ministries of **New Fadama Seventh-day Adventist Church**.

The app is a Django site: browser, Django templates with HTMX, and PostgreSQL. Development and deployment both use Docker Compose with two containers only — the Django application and PostgreSQL.

## Run it

```sh
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py seed_dev_data
```

Open http://127.0.0.1:8000/

PostgreSQL is published on the host at port **5433** so it does not collide with another Postgres on 5432. Inside Compose the app still connects to `db:5432`.

Development sign-in, from the seed command only:

| Username | Password | Role |
| --- | --- | --- |
| `admin` | `dev-only-change-me` | Administrator (superuser) |
| `coordinator` | `dev-only-change-me` | Coordinator |
| `teacher` | `dev-only-change-me` | Teacher |

These passwords are for local development. Production refuses the development `SECRET_KEY` and refuses the seed command.

## What it does

- Children, parents and guardians, and classes from Pre-school through SHS 3
- Sabbath attendance for the coming or current Saturday, in `Africa/Accra`
- Present and absent only
- Missing-church streaks that count recorded absences and skip Sabbaths with no record
- Birthdays and age, calculated from the date of birth
- Search, filters, and CSV reports
- Roles: Administrator, Coordinator, and Teacher

## Stack

| Piece | Version |
| --- | --- |
| Python image | 3.14.8 |
| Django | 6.1.1 |
| PostgreSQL image | 18.4 |
| HTMX | 2.0.11, vendored in `static/js/htmx.min.js` |
| Tailwind CSS | 4.3.3 |
| Gunicorn | 26.2.0 |
| WhiteNoise | 6.12.0 |

WhiteNoise serves static files from the Django container. There is no Nginx, Redis, Celery, or frontend container.

Further reading is in [docs/](docs/architecture.md).
