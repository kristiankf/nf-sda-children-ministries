from datetime import date

from django.db.models import Count, Q

from apps.attendance.models import Attendance
from apps.children.models import Child


def sabbath_stats(day: date) -> dict:
    active_children = Child.objects.filter(status=Child.Status.ACTIVE).count()
    counts = Attendance.objects.filter(date=day, child__status=Child.Status.ACTIVE).aggregate(
        present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
        absent=Count("id", filter=Q(status=Attendance.Status.ABSENT)),
        recorded=Count("id"),
    )
    present = counts["present"] or 0
    absent = counts["absent"] or 0
    recorded = counts["recorded"] or 0
    marked = present + absent
    return {
        "date": day,
        "present": present,
        "absent": absent,
        "recorded": recorded,
        "active_children": active_children,
        "unmarked": max(active_children - marked, 0),
        "is_recorded": recorded > 0,
        "rate": round(100 * present / marked) if marked else None,
    }
