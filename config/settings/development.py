"""Local Docker Compose settings. Debug stays on in this module."""

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = env_list(  # noqa: F405
    "ALLOWED_HOSTS",
    ["localhost", "127.0.0.1", "web"],
)
EMAIL_BACKEND = env(  # noqa: F405
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
