from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def ministry_permission_required(*permissions: str):
    """Require every permission. Anonymous users are sent to the login page."""

    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.has_perms(permissions):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
