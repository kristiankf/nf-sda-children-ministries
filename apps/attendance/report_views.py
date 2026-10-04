import csv
from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import render

from apps.attendance.calendar import latest_sabbath_on_or_before
from apps.attendance.models import Attendance
from apps.attendance.streaks import missing_church
from apps.attendance.views import _parse_date
from apps.children.groups import attach_ministry_groups
from apps.children.models import Child
from apps.core import dates
from apps.core.auth import ministry_permission_required
from apps.schools.levels import ClassLevel


def _report_queryset(request, start, end):
    children = Child.objects.filter(status=Child.Status.ACTIVE).select_related(
        "sabbath_class_override"
    )
    class_level = request.GET.get("class_level") or ""
    child_id = request.GET.get("child") or ""
    if class_level == "none":
        children = children.filter(class_level="")
    elif class_level in ClassLevel.values:
        children = children.filter(class_level=class_level)
    if str(child_id).isdigit():
        children = children.filter(pk=int(child_id))
    date_filter = Q(attendance_records__date__gte=start, attendance_records__date__lte=end)
    return children.annotate(
        present_count=Count(
            "attendance_records",
            filter=date_filter & Q(attendance_records__status=Attendance.Status.PRESENT),
        ),
        absent_count=Count(
            "attendance_records",
            filter=date_filter & Q(attendance_records__status=Attendance.Status.ABSENT),
        ),
    ).order_by("last_name", "first_name", "pk")


def _bounds(request):
    today = dates.local_today()
    end = _parse_date(request.GET.get("date_to"), latest_sabbath_on_or_before(today))
    start = _parse_date(request.GET.get("date_from"), end - timedelta(days=49))
    if start > end:
        start, end = end, start
    return start, end, today


def _decorate(children, streak_map, today):
    decorated = []
    for child in attach_ministry_groups(children, today):
        marked = child.present_count + child.absent_count
        child.absence_weeks = streak_map.get(child.pk, 0)
        child.attendance_rate = round(100 * child.present_count / marked) if marked else None
        decorated.append(child)
    return decorated


@ministry_permission_required("attendance.view_attendance")
def attendance_report(request):
    start, end, today = _bounds(request)
    children = _report_queryset(request, start, end)
    totals = children.aggregate(present=Sum("present_count"), absent=Sum("absent_count"))
    present = totals["present"] or 0
    absent = totals["absent"] or 0
    marked = present + absent
    streak_map = {row["child_id"]: row["weeks"] for row in missing_church(today, minimum=1)}
    page = Paginator(children, 50).get_page(request.GET.get("page"))
    return render(
        request,
        "reports/attendance.html",
        {
            "page_obj": page,
            "children": _decorate(page.object_list, streak_map, today),
            "start": start,
            "end": end,
            "present": present,
            "absent": absent,
            "rate": round(100 * present / marked) if marked else None,
            "class_levels": ClassLevel.choices,
        },
    )


@ministry_permission_required("attendance.view_attendance")
def attendance_csv(request):
    start, end, today = _bounds(request)
    streak_map = {row["child_id"]: row["weeks"] for row in missing_church(today, minimum=1)}
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="sabbath-attendance.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(
        [
            "Child",
            "Sabbath class",
            "Youth group",
            "School",
            "Class",
            "Present",
            "Absent",
            "Attendance %",
            "Current absence streak (weeks)",
        ]
    )
    for child in _decorate(_report_queryset(request, start, end), streak_map, today):
        writer.writerow(
            [
                child.full_name,
                child.sabbath_class.name if child.sabbath_class else "",
                child.youth_group.name if child.youth_group else "",
                child.school_name,
                child.get_class_level_display() if child.class_level else "",
                child.present_count,
                child.absent_count,
                "" if child.attendance_rate is None else child.attendance_rate,
                child.absence_weeks,
            ]
        )
    return response
