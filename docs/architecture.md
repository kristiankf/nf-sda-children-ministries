# Architecture

The site is one Django project. The browser talks to Django. Django talks to PostgreSQL. HTMX updates fragments of a page, such as the child search results, without a separate API.

```text
Browser
  → Django templates + HTMX
    → PostgreSQL
```

## Containers

`compose.yaml` is the development environment. `compose.prod.yaml` is a complete production file, not an override, so volume settings do not merge by accident.

| Service | Image | Role |
| --- | --- | --- |
| `web` | Built from the `development` or `production` Dockerfile target | Django |
| `db` | `postgres:18.4` | Database |

Development bind-mounts the source into `web` and publishes Postgres on host port 5433. Production does not mount the source, does not publish Postgres, stores uploaded photos on a `media` volume, and runs Gunicorn with two workers.

The image has three stages:

- `assets` builds Tailwind CSS. Only the production target copies that CSS in.
- `development` installs Ruff and runs `runserver`.
- `production` runs Gunicorn. WhiteNoise serves the collected static files, including the CSS built in `assets`.

`docker/entrypoint.sh` waits for Postgres, migrates, creates `staticfiles/` and `media/`, and runs `collectstatic` when `COLLECT_STATIC=1`.

## Applications

| App | Responsibility |
| --- | --- |
| `apps.core` | Shared models, dates, phones, dashboard, reports index |
| `apps.accounts` | Login, logout, password change, role groups |
| `apps.children` | Child records, search, guardians, photos, birthday report, children totals |
| `apps.parents` | Parent records |
| `apps.schools` | Class ladder, academic year, class placements |
| `apps.attendance` | Sabbath roll, history, streaks, attendance report |

There is no custom user model. People who sign in are Django users. Children and parents are not users.

## Request path

Pages are server-rendered. A few forms use HTMX:

- Child and parent lists refetch their result markup on search.
- Adding a guardian searches existing parents.

The Sabbath roll search is local JavaScript. It hides rows. The form still posts every child.

## Static files and email

Development uses Django's static finders and the console email backend. Production uses WhiteNoise's compressed manifest storage. Reminder-style information on the dashboard is a database query, not a scheduled job. Outbound email, when configured, uses Django's SMTP settings.

## What is intentionally absent

No Redis, Celery, Nginx, object storage, message bus, or second web framework. HTTPS, if used, is terminated on the host in front of the Django container. See [deployment.md](deployment.md) and [decisions.md](decisions.md).
