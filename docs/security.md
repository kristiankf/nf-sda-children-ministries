# Security

Ministry data is children's names, birth dates, phones, addresses, and optional photos. Treat the deployment as a private application.

## Authentication and roles

Every ministry page requires a signed-in user. Views that change data check Django permissions. A missing permission is a 403, not a hidden button alone. Teachers can record and correct attendance, including clearing a mark, and cannot create or edit children, parents, or the academic year. Coordinators can. Administrators have every permission.

Logout is a POST with a CSRF token. Passwords use Django's validators and the built-in password change form.

Groups are recreated idempotently after migrate. Removing a permission in the admin can be overwritten the next time `ensure_ministry_roles` runs. Change `apps/accounts/roles.py` if a role should permanently differ.

## Production guards

`config.settings.production` will not boot with the development secret or an empty `ALLOWED_HOSTS`. `DEBUG` is off. With `USE_HTTPS=true`, cookies are marked secure and the SSL redirect uses the proxy header. HSTS stays at 0 until `SECURE_HSTS_SECONDS` is set.

Uploaded files are limited to 6 MB at the request and 5 MB on the photo field. Content type is checked for JPEG, PNG, and WebP. Filenames are generated. The photo response sets `X-Content-Type-Options: nosniff` and a private cache header.

## Phones and search

Phones are normalized before save. Search digits are normalized too, so a local `024…` query matches a stored `+233…` number. Validation errors stay on the form.

## Data retention

Attendance rows are not deleted when a child leaves. Status becomes inactive or transferred, and the child drops off the roll and the active reports. Historical rows remain.

## Secrets

`.env` is gitignored. `.env.example` holds development placeholders only. Do not commit a production `SECRET_KEY`, database password, or SMTP password. The development accounts `admin`, `coordinator`, and `teacher` with password `dev-only-change-me` exist only after `seed_dev_data`.

## Headers

`robots` is `noindex, nofollow`. Clickjacking protection is Django's `XFrameOptionsMiddleware`. There is no public self-registration.
