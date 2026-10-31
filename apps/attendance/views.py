import csv
from datetime import datetime, timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.formats import date_format

from apps.attendance.calendar import (
    current_sabbath,
    is_sabbath,
    latest_sabbath_on_or_before,
    upcoming_sabbath,
)
from apps.attendance.models import Attendance
from apps.attendance.permissions import can_edit_past_attendance, can_record_attendance_for
from apps.attendance.stats import sabbath_stats
from apps.attendance.streaks import missing_church
from apps.children.groups import attach_ministry_groups, load_bands
from apps.children.models import AgeGroup, Child
from apps.core import dates
from apps.core.auth import ministry_permission_required
from apps.visitors.queries import visits_on


def _parse_date(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return fallback


def _sabbath_division(value: str | None) -> str:
    slug = (value or "").strip()
    if slug and AgeGroup.objects.filter(kind=AgeGroup.Kind.SABBATH, slug=slug).exists():
        return slug
    return ""


def _roll_children(selected, today):
    children = list(
        Child.objects.filter(status=Child.Status.ACTIVE)
        .select_related("sabbath_class_override")
        .order_by("last_name", "first_name", "pk")
    )
    attach_ministry_groups(children, today)
    existing = {
        record.child_id: record.status
        for record in Attendance.objects.filter(date=selected, child__status=Child.Status.ACTIVE)
    }
    for child in children:
        child.roll_status = existing.get(child.pk, "")
    return children, existing


def _present_children(selected, today):
    children = list(
        Child.objects.filter(
            status=Child.Status.ACTIVE,
            attendance_records__date=selected,
            attendance_records__status=Attendance.Status.PRESENT,
        )
        .select_related("sabbath_class_override")
        .order_by("last_name", "first_name", "pk")
        .distinct()
    )
    attach_ministry_groups(children, today)
    return children


def _nav_dates(selected, today):
    previous_date = selected - timedelta(days=7) if is_sabbath(selected) else None
    next_candidate = selected + timedelta(days=7) if is_sabbath(selected) else None
    open_through = upcoming_sabbath(today)
    next_date = next_candidate if next_candidate and next_candidate <= open_through else None
    return previous_date, next_date


def _date_shell_context(selected, current, today, request):
    previous_date, next_date = _nav_dates(selected, today)
    return {
        "selected": selected,
        "current_sabbath": current,
        "today": today,
        "is_sabbath": is_sabbath(selected),
        "previous_date": previous_date,
        "next_date": next_date,
        "selected_division": _sabbath_division(request.GET.get("division")),
        "can_edit_past": can_edit_past_attendance(request.user),
    }


@ministry_permission_required("attendance.view_attendance")
def roll(request):
    today = dates.local_today()
    current = current_sabbath(today)
    raw_date = request.POST.get("date") if request.method == "POST" else request.GET.get("date")
    selected = _parse_date(raw_date, current)

    if not is_sabbath(selected):
        return render(
            request,
            "attendance/roll_invalid.html",
            {
                **_date_shell_context(selected, current, today, request),
                "mode": "invalid",
            },
        )

    if selected > current:
        return render(
            request,
            "attendance/roll_future.html",
            {
                **_date_shell_context(selected, current, today, request),
                "mode": "future",
                "stats": sabbath_stats(selected),
            },
        )

    is_past = selected < current
    editing = (not is_past) or (
        is_past and request.GET.get("edit") == "1" and can_edit_past_attendance(request.user)
    )

    if request.method == "POST":
        if not can_record_attendance_for(request.user, selected=selected, current=current):
            raise PermissionDenied
        children, _existing = _roll_children(selected, today)
        _save_roll(children, request.POST, selected, request.user)
        messages.success(
            request, f"Attendance for {date_format(selected, 'l, j F Y')} has been saved."
        )
        division = _sabbath_division(request.POST.get("division"))
        target = f"{reverse('attendance:roll')}?date={selected.isoformat()}"
        if is_past:
            target = f"{target}&edit=1"
        if division:
            target = f"{target}&division={division}"
        return redirect(target)

    if not editing:
        present_children = _present_children(selected, today)
        visitors = list(visits_on(selected))
        return render(
            request,
            "attendance/roll_summary.html",
            {
                **_date_shell_context(selected, current, today, request),
                "mode": "summary",
                "stats": sabbath_stats(selected),
                "present_children": present_children,
                "visitors": visitors,
            },
        )

    children, existing = _roll_children(selected, today)
    sabbath_classes, _youth_groups = load_bands()
    return render(
        request,
        "attendance/roll.html",
        {
            **_date_shell_context(selected, current, today, request),
            "mode": "edit",
            "is_past": is_past,
            "is_future": False,
            "children": children,
            "existing": existing,
            "stats": sabbath_stats(selected),
            "present_value": Attendance.Status.PRESENT,
            "absent_value": Attendance.Status.ABSENT,
            "sabbath_classes": sabbath_classes,
            "can_save": can_record_attendance_for(request.user, selected=selected, current=current),
        },
    )


def _save_roll(children, post, selected, user) -> None:
    with transaction.atomic():
        for child in children:
            key = f"status_{child.pk}"
            if key not in post:
                continue
            status = post.get(key)
            if status in {Attendance.Status.PRESENT, Attendance.Status.ABSENT}:
                record, created = Attendance.objects.get_or_create(
                    child=child,
                    date=selected,
                    defaults={
                        "status": status,
                        "recorded_by": user,
                        "created_by": user,
                        "updated_by": user,
                    },
                )
                if not created and (record.status != status or record.recorded_by_id != user.id):
                    record.status = status
                    record.recorded_by = user
                    record.updated_by = user
                    record.save(update_fields=["status", "recorded_by", "updated_by", "updated_at"])
            elif status == "UNMARKED":
                Attendance.objects.filter(child=child, date=selected).delete()


@ministry_permission_required("attendance.view_attendance")
def roll_csv(request):
    today = dates.local_today()
    current = current_sabbath(today)
    selected = _parse_date(request.GET.get("date"), current)
    if not is_sabbath(selected) or selected > current:
        raise PermissionDenied

    present_children = _present_children(selected, today)
    visitors = list(visits_on(selected))
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="sabbath-{selected.isoformat()}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Type", "Name", "Sabbath class", "Came with", "Reason"])
    for child in present_children:
        sabbath_class = child.sabbath_class.name if child.sabbath_class else ""
        writer.writerow(["Child", child.full_name, sabbath_class, "", ""])
    for visit in visitors:
        writer.writerow(
            [
                "Visitor",
                visit.visitor.full_name,
                "",
                visit.came_with_label,
                visit.reason,
            ]
        )
    return response


@ministry_permission_required("attendance.view_attendance")
def history(request):
    rows = (
        Attendance.objects.values("date")
        .annotate(
            present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
            absent=Count("id", filter=Q(status=Attendance.Status.ABSENT)),
        )
        .order_by("-date")
    )
    page = Paginator(rows, 12).get_page(request.GET.get("page"))
    for row in page.object_list:
        row["is_sabbath"] = is_sabbath(row["date"])
    return render(request, "attendance/history.html", {"page_obj": page})


@ministry_permission_required("attendance.view_attendance")
def missing(request):
    today = dates.local_today()
    return render(
        request,
        "attendance/missing.html",
        {
            "rows": missing_church(today, minimum=1),
            "cutoff": latest_sabbath_on_or_before(today),
        },
    )
