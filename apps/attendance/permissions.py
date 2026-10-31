"""Who may change attendance for the current vs a past Sabbath."""

from apps.accounts.roles import ROLE_ADMIN, ROLE_COORDINATOR


def can_edit_past_attendance(user) -> bool:
    """Coordinators and admins may open the edit UI for a past Sabbath."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name__in=[ROLE_ADMIN, ROLE_COORDINATOR]).exists()


def can_record_attendance_for(user, *, selected, current) -> bool:
    """Teachers record the current Sabbath only; coordinators may also edit past."""
    if not user.has_perms(["attendance.add_attendance", "attendance.change_attendance"]):
        return False
    if selected == current:
        return True
    if selected < current:
        return can_edit_past_attendance(user)
    return False
