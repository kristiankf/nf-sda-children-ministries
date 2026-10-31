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
| `apps.attendance` | Current/past Sabbath roll, history, streaks, attendance report, Sabbath CSV |
| `apps.visitors` | Visitor records, Sabbath visits, follow-up, convert to child |

There is no custom user model. People who sign in are Django users. Children and parents are not users.

## Request path

Pages are server-rendered. A few forms use HTMX:

- Child and parent lists refetch their result markup on search.
- Adding a guardian searches existing parents.
- A parent detail page can link one or more children, with search that keeps current selections.
- Adding a child can optionally open a parent modal that searches existing parents or collects first name, last name, and phone.
- School and address on the child form suggest values already saved on other children as you type.
- Add visitor searches returning visitors and companion parents or children.

The Sabbath roll search is local JavaScript. It hides rows. The form still posts every child. Past Sabbaths use a summary template; Edit opens the live roll for coordinators and admins.

## Static files and email

Development uses Django's static finders and the console email backend. Production uses WhiteNoise's compressed manifest storage with a long browser cache. `GZipMiddleware` compresses HTML and other compressible responses (WhiteNoise already serves pre-compressed static files). Reminder-style information on the dashboard is a database query, not a scheduled job. Outbound email, when configured, uses Django's SMTP settings.

The academic calendar check on signed-in requests remembers the open year in process memory for the Accra calendar day, so Postgres is not hit on every page view while that year is still open. Editing the year dates clears the memo.

## What is intentionally absent

No Redis, Celery, Nginx, object storage, message bus, or second web framework. HTTPS, if used, is terminated on the host in front of the Django container. See [deployment.md](deployment.md) and [decisions.md](decisions.md).
