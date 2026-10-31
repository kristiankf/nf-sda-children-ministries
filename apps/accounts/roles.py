"""Ministry roles stored as Django groups."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

ROLE_ADMIN = "ADMIN"
ROLE_COORDINATOR = "COORDINATOR"
ROLE_TEACHER = "TEACHER"

# Teacher and Coordinator share the same ministry model permissions for now.
# Only ADMIN is staff/superuser; Django admin is not part of these groups.
MINISTRY_MODELS = [
    ("children", "child"),
    ("parents", "parent"),
    ("parents", "childguardian"),
    ("schools", "academicyear"),
    ("attendance", "attendance"),
    ("children", "agegroup"),
    ("visitors", "visitor"),
    ("visitors", "visit"),
]


def _ministry_permissions() -> list[Permission]:
    permissions: list[Permission] = []
    for app_label, model in MINISTRY_MODELS:
        permissions.extend(
            Permission.objects.filter(content_type__app_label=app_label, content_type__model=model)
        )
    return permissions


def ensure_ministry_roles(sender=None, **kwargs) -> None:
    """Create groups once ministry content types exist. Safe to run repeatedly."""
    if not ContentType.objects.filter(app_label="attendance", model="attendance").exists():
        return

    ministry_permissions = _ministry_permissions()

    teacher, _created = Group.objects.get_or_create(name=ROLE_TEACHER)
    teacher.permissions.set(ministry_permissions)

    coordinator, _created = Group.objects.get_or_create(name=ROLE_COORDINATOR)
    coordinator.permissions.set(ministry_permissions)

    admin, _created = Group.objects.get_or_create(name=ROLE_ADMIN)
    admin.permissions.set(Permission.objects.all())
