"""Academic years and the class move that follows one.

There is no scheduler. A signed-in request checks the open year, and when its
end date has passed every active child moves up one class.
"""

from contextvars import ContextVar
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from apps.core.dates import local_today
from apps.schools.levels import next_class_level
from apps.schools.models import AcademicYear, ClassPlacement

_advancing = ContextVar("academic_calendar_advancing", default=False)
MAX_CATCH_UP_YEARS = 15


def period_containing(day: date) -> tuple[date, date, str]:
    """The September–August year that contains `day`."""
    start_year = day.year if (day.month, day.day) >= (9, 1) else day.year - 1
    start = date(start_year, 9, 1)
    end = date(start_year + 1, 8, 31)
    return start, end, f"{start_year}/{start_year + 1}"


def period_after(previous_end: date) -> tuple[date, date, str]:
    """The year that starts the day after `previous_end` and lasts one year."""
    start = previous_end + timedelta(days=1)
    try:
        next_start = date(start.year + 1, start.month, start.day)
    except ValueError:
        next_start = date(start.year + 1, 3, 1)
    end = next_start - timedelta(days=1)
    return start, end, f"{start.year}/{end.year}"


def advance_academic_calendar(today: date | None = None) -> AcademicYear:
    """Open the current year, and move classes forward when the open year has ended."""
    today = today or local_today()
    current = AcademicYear.objects.filter(is_current=True).only("end_date").first()
    if current is not None and current.end_date >= today:
        return AcademicYear.objects.get(pk=current.pk)
    return _advance_locked(today)


def sync_current_placement(child) -> None:
    """Store this child's class on the open academic year."""
    if _advancing.get() or not child.pk:
        return
    year = advance_academic_calendar()
    level = type(child).objects.filter(pk=child.pk).values_list("class_level", flat=True).first()
    if level:
        ClassPlacement.objects.update_or_create(
            child_id=child.pk,
            academic_year=year,
            defaults={"class_level": level},
        )
    else:
        ClassPlacement.objects.filter(child_id=child.pk, academic_year=year).delete()


def _advance_locked(today: date) -> AcademicYear:
    token = _advancing.set(True)
    try:
        with transaction.atomic():
            current = AcademicYear.objects.select_for_update().filter(is_current=True).first()
            if current is None:
                current = _open_period_containing(today)
                _backfill_placements(current)
            steps = 0
            while current.end_date < today and steps < MAX_CATCH_UP_YEARS:
                current = _progress(current)
                steps += 1
            return current
    finally:
        _advancing.reset(token)


def _open_period_containing(today: date) -> AcademicYear:
    start, end, name = period_containing(today)
    year = AcademicYear.objects.filter(name=name).first()
    if year is None:
        year = AcademicYear.objects.create(
            name=name,
            start_date=start,
            end_date=end,
            is_current=False,
        )
    _mark_current(year)
    return year


def _progress(closed: AcademicYear) -> AcademicYear:
    from apps.children.models import Child

    start, end, name = period_after(closed.end_date)
    opened = _year_for_period(name, start, end, closed_pk=closed.pk)
    now = timezone.now()
    active = Child.objects.filter(status=Child.Status.ACTIVE).exclude(class_level="")
    for child in active:
        ClassPlacement.objects.update_or_create(
            child=child,
            academic_year=closed,
            defaults={"class_level": child.class_level},
        )
        new_level = next_class_level(child.class_level)
        if new_level != child.class_level:
            Child.objects.filter(pk=child.pk).update(class_level=new_level, updated_at=now)
        ClassPlacement.objects.update_or_create(
            child=child,
            academic_year=opened,
            defaults={"class_level": new_level},
        )
    _mark_current(opened)
    return opened


def _backfill_placements(year: AcademicYear) -> None:
    from apps.children.models import Child

    children = Child.objects.filter(status=Child.Status.ACTIVE).exclude(class_level="")
    existing = set(
        ClassPlacement.objects.filter(academic_year=year).values_list("child_id", flat=True)
    )
    for child in children:
        if child.pk in existing:
            continue
        ClassPlacement.objects.create(
            child=child,
            academic_year=year,
            class_level=child.class_level,
        )


def _year_for_period(name: str, start: date, end: date, closed_pk: int) -> AcademicYear:
    existing = AcademicYear.objects.filter(name=name).exclude(pk=closed_pk).first()
    if existing is not None and existing.start_date == start and existing.end_date == end:
        return existing
    if existing is not None or AcademicYear.objects.filter(name=name, pk=closed_pk).exists():
        name = _free_name(name)
    return AcademicYear.objects.create(
        name=name,
        start_date=start,
        end_date=end,
        is_current=False,
    )


def _free_name(base: str) -> str:
    for number in range(2, 20):
        candidate = f"{base[:16]}-{number}"
        if not AcademicYear.objects.filter(name=candidate).exists():
            return candidate
    return f"{base[:12]}-{timezone.now().strftime('%H%M%S')}"[:20]


def _mark_current(year: AcademicYear) -> None:
    AcademicYear.objects.filter(is_current=True).exclude(pk=year.pk).update(is_current=False)
    if not year.is_current:
        year.is_current = True
        year.save(update_fields=["is_current", "updated_at"])
