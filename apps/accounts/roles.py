"""Ministry roles stored as Django groups."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

ROLE_ADMIN = "ADMIN"
ROLE_COORDINATOR = "COORDINATOR"
ROLE_TEACHER = "TEACHER"

TEACHER_PERMISSIONS = [
    "children.view_child",
    "parents.view_parent",
    "parents.view_childguardian",
    "schools.view_academicyear",
    "attendance.view_attendance",
    "attendance.add_attendance",
    "attendance.change_attendance",
    "attendance.delete_attendance",
]

COORDINATOR_MODELS = [
    ("children", "child"),
    ("parents", "parent"),
    ("parents", "childguardian"),
    ("schools", "academicyear"),
    ("attendance", "attendance"),
    ("children", "agegroup"),
]


def _permission(code: str) -> Permission:
    app_label, codename = code.split(".", 1)
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def ensure_ministry_roles(sender=None, **kwargs) -> None:
    """Create groups once ministry content types exist. Safe to run repeatedly."""
    if not ContentType.objects.filter(app_label="attendance", model="attendance").exists():
        return

    teacher_permissions = [_permission(code) for code in TEACHER_PERMISSIONS]
    coordinator_permissions = []
    for app_label, model in COORDINATOR_MODELS:
        coordinator_permissions.extend(
            Permission.objects.filter(content_type__app_label=app_label, content_type__model=model)
        )

    teacher, _created = Group.objects.get_or_create(name=ROLE_TEACHER)
    teacher.permissions.set(teacher_permissions)

    coordinator, _created = Group.objects.get_or_create(name=ROLE_COORDINATOR)
    coordinator.permissions.set(coordinator_permissions)

    admin, _created = Group.objects.get_or_create(name=ROLE_ADMIN)
    admin.permissions.set(Permission.objects.all())
