"""Production settings for a single Django container behind optional TLS."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

if SECRET_KEY in {"", "dev-only-change-me"}:  # noqa: F405
    raise ImproperlyConfigured("Set a unique SECRET_KEY before running in production.")

if not ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("Set ALLOWED_HOSTS before running in production.")

USE_HTTPS = env_bool("USE_HTTPS", False)  # noqa: F405
if USE_HTTPS:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)  # noqa: F405
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "0") or "0")  # noqa: F405
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
    SECURE_HSTS_PRELOAD = False

STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 30
