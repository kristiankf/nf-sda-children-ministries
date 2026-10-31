from apps.schools.calendar import ensure_academic_calendar


class AcademicCalendarMiddleware:
    """Move classes up once the open academic year has ended.

    Runs for signed-in requests only, so the login page does not write rows.
    Remembers an open year for the Accra day in process memory so most requests
    do not hit Postgres for this check.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            ensure_academic_calendar()
        return self.get_response(request)
