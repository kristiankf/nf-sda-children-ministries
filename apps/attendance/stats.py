from datetime import date

from django.db.models import Count, Q

from apps.attendance.models import Attendance
from apps.children.models import Child
from apps.visitors.models import Visit


def sabbath_stats(day: date) -> dict:
    active_children = Child.objects.filter(status=Child.Status.ACTIVE).count()
    counts = Attendance.objects.filter(date=day, child__status=Child.Status.ACTIVE).aggregate(
        present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
        absent=Count("id", filter=Q(status=Attendance.Status.ABSENT)),
        recorded=Count("id"),
    )
    children_present = counts["present"] or 0
    absent = counts["absent"] or 0
    recorded = counts["recorded"] or 0
    visitors = Visit.objects.filter(date=day).count()
    present = children_present + visitors
    marked = children_present + absent
    accounted = marked + visitors
    return {
        "date": day,
        "present": present,
        "children_present": children_present,
        "visitors": visitors,
        "absent": absent,
        "recorded": recorded,
        "active_children": active_children,
        "unmarked": max(active_children - marked, 0),
        "is_recorded": recorded > 0 or visitors > 0,
        "rate": round(100 * present / accounted) if accounted else None,
    }
