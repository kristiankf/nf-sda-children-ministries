# Deployment

Production is the same two containers, started from `compose.prod.yaml`:

```sh
docker compose -f compose.prod.yaml up -d --build
```

That file does not extend `compose.yaml`. Postgres is not published to the host. The app listens on port 8000. Uploaded photos persist in the `media` volume. Restart policy is `unless-stopped`.

## Settings

`DJANGO_SETTINGS_MODULE` is `config.settings.production`. `DEBUG` is forced off. The process refuses to start if `SECRET_KEY` is empty or still `dev-only-change-me`, or if `ALLOWED_HOSTS` is empty.

Set a real `.env` on the server:

- `SECRET_KEY` — long random string
- `ALLOWED_HOSTS` — the public hostname
- `CSRF_TRUSTED_ORIGINS` — `https://` origin when TLS is on, or the `http://` origin when it is not
- `POSTGRES_PASSWORD` — required; the compose file has no default
- `DATABASE_URL` — `postgresql://USER:PASSWORD@db:5432/DATABASE`
- `COLLECT_STATIC=1` is set by the compose file

Create users with `docker compose -f compose.prod.yaml exec web python manage.py createsuperuser`, then add ministry users in Django admin and assign groups. Do not run `seed_dev_data` on a production database. The command exits when `DEBUG` is off.

## Static files and photos

Gunicorn does not serve static files. WhiteNoise, inside the Django container, serves the files collected at startup. The production image rebuilds `static/css/app.css` from the Tailwind sources.

Child photos are not under the public media URL. A signed-in user loads them through the child photo view.

## TLS

`USE_HTTPS` defaults to false so the two containers can serve plain HTTP on a private network. When a TLS proxy on the host forwards to port 8000, set:

```text
USE_HTTPS=true
SECURE_SSL_REDIRECT=true
```

The app then marks session and CSRF cookies secure, redirects HTTP to HTTPS, and trusts `X-Forwarded-Proto`. Set `SECURE_HSTS_SECONDS` only after HTTPS is confirmed. The proxy is part of the host, not a third Compose service. Do not add Nginx to this stack for that job.

## Backups

Back up the Postgres volume and the `media` volume. A database dump from inside the network is enough for the relational data:

```sh
docker compose -f compose.prod.yaml exec db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"
```

Restoring that dump does not restore photo files. Copy the `media` volume as well.

## A small VPS

One small Linux VM can run both containers. Give Postgres most of the memory if you have to choose. Two Gunicorn workers is the default in the image; raise it only when the machine has the RAM. Put the TLS certificate on the host proxy, point it at `127.0.0.1:8000`, and leave Postgres unpublished.
