from datetime import datetime, timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.formats import date_format

from apps.attendance.calendar import is_sabbath, latest_sabbath_on_or_before, upcoming_sabbath
from apps.attendance.models import Attendance
from apps.attendance.stats import sabbath_stats
from apps.attendance.streaks import missing_church
from apps.children.groups import attach_ministry_groups, load_bands
from apps.children.models import AgeGroup, Child
from apps.core import dates
from apps.core.auth import ministry_permission_required


def _parse_date(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return fallback


@ministry_permission_required("attendance.view_attendance")
def roll(request):
    today = dates.local_today()
    default_date = upcoming_sabbath(today)
    raw_date = request.POST.get("date") if request.method == "POST" else request.GET.get("date")
    selected = _parse_date(raw_date, default_date)
    if selected > upcoming_sabbath(today):
        messages.error(
            request,
            "Choose the coming Sabbath or an earlier date. Later dates are not open yet.",
        )
        selected = default_date
    is_future = selected > today

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

    if request.method == "POST":
        if not request.user.has_perms(
            ["attendance.add_attendance", "attendance.change_attendance"]
        ):
            raise PermissionDenied
        if is_future:
            when = date_format(selected, "l, j F Y")
            messages.error(
                request,
                f"Attendance for {when} cannot be saved until that day.",
            )
        else:
            _save_roll(children, request.POST, selected, request.user)
            messages.success(
                request, f"Attendance for {date_format(selected, 'l, j F Y')} has been saved."
            )
        division = _sabbath_division(request.POST.get("division"))
        target = f"{reverse('attendance:roll')}?date={selected.isoformat()}"
        if division:
            target = f"{target}&division={division}"
        return redirect(target)

    previous_date = (
        selected - timedelta(days=7)
        if is_sabbath(selected)
        else latest_sabbath_on_or_before(selected - timedelta(days=1))
    )
    next_date = (
        selected + timedelta(days=7)
        if is_sabbath(selected)
        else upcoming_sabbath(selected + timedelta(days=1))
    )
    sabbath_classes, _youth_groups = load_bands()
    return render(
        request,
        "attendance/roll.html",
        {
            "selected": selected,
            "is_future": is_future,
            "children": children,
            "existing": existing,
            "stats": sabbath_stats(selected),
            "is_sabbath": is_sabbath(selected),
            "previous_date": previous_date,
            "next_date": next_date if next_date <= upcoming_sabbath(today) else None,
            "present_value": Attendance.Status.PRESENT,
            "absent_value": Attendance.Status.ABSENT,
            "sabbath_classes": sabbath_classes,
            "selected_division": _sabbath_division(request.GET.get("division")),
        },
    )


def _sabbath_division(value: str | None) -> str:
    slug = (value or "").strip()
    if slug and AgeGroup.objects.filter(kind=AgeGroup.Kind.SABBATH, slug=slug).exists():
        return slug
    return ""


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
