# Setup

Requirements on the machine that runs Compose: Docker, and Node.js if you change templates or CSS. The app itself runs inside the image (`python:3.14.8-slim`). You do not need a host virtualenv or a host Postgres.

## First run

From the project directory:

```sh
cp .env.example .env
docker compose up -d --build
```

The first build installs Python packages and Ruff. Postgres stores data in the `pgdata` volume, mounted at `/var/lib/postgresql` (PostgreSQL 18 keeps its data in a versioned subdirectory of that path).

When `web` is up:

```sh
docker compose exec web python manage.py seed_dev_data
```

The seed command loads fictional children, families, and Sabbath attendance relative to the latest Saturday on or before today. It refuses to run when `DEBUG` is off.

## Host ports

| Published port | Service |
| --- | --- |
| 8000 | Django |
| 5433 | PostgreSQL, mapped to 5432 in the container |

Port 5432 is left free because other local projects often use it. Change the mapping in `compose.yaml` if 5433 is taken, and point any host database tool at the new port. The app's `DATABASE_URL` should keep using `db:5432`.

## Sign in

http://127.0.0.1:8000/accounts/login/

`admin`, `coordinator`, and `teacher` all use `dev-only-change-me` after seeding. Create real users in Django admin and put them in the `ADMIN`, `COORDINATOR`, or `TEACHER` group.

## CSS

`static/css/app.css` is already built. After editing `assets/app.css` or class names in templates:

```sh
npm install
npm run build:css
```

HTMX 2.0.11 is already in `static/js/htmx.min.js`.

## Stop

```sh
docker compose down
```

`docker compose down -v` deletes the database volume.
