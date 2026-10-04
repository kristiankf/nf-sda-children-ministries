"""Consecutive Sabbath absences.

A Sabbath counts only when this child has an attendance row on that Saturday.
ABSENT adds one week. PRESENT ends the streak. A Saturday with no row is not
an absence and does not end the streak. Dates after `cutoff` are ignored, so
a Sabbath that has not arrived yet cannot mark a child absent.
"""

from collections import defaultdict
from datetime import date

from apps.attendance.calendar import latest_sabbath_on_or_before
from apps.attendance.models import Attendance
from apps.children.models import Child
from apps.parents.models import ChildGuardian

PRESENT = Attendance.Status.PRESENT
ABSENT = Attendance.Status.ABSENT


def consecutive_absence_weeks(records, *, cutoff: date) -> int:
    relevant = [
        (record_date, status)
        for record_date, status in records
        if record_date <= cutoff and record_date.weekday() == 5
    ]
    relevant.sort(key=lambda item: item[0], reverse=True)
    weeks = 0
    for _record_date, status in relevant:
        if status == PRESENT:
            break
        if status == ABSENT:
            weeks += 1
    return weeks


def missing_church(as_of: date, *, minimum: int = 1) -> list[dict]:
    cutoff = latest_sabbath_on_or_before(as_of)
    rows = Attendance.objects.filter(
        child__status=Child.Status.ACTIVE,
        date__lte=cutoff,
        date__week_day=7,
    ).values_list(
        "child_id",
        "child__first_name",
        "child__last_name",
        "child__preferred_name",
        "date",
        "status",
    )
    grouped: dict[int, list[tuple[date, str]]] = defaultdict(list)
    labels: dict[int, str] = {}
    for child_id, first_name, last_name, preferred_name, record_date, status in rows:
        grouped[child_id].append((record_date, status))
        given = preferred_name or first_name
        labels[child_id] = f"{given} {last_name}".strip()

    results = []
    for child_id, records in grouped.items():
        weeks = consecutive_absence_weeks(records, cutoff=cutoff)
        if weeks >= minimum:
            results.append(
                {
                    "child_id": child_id,
                    "name": labels[child_id],
                    "weeks": weeks,
                }
            )
    results.sort(key=lambda item: (-item["weeks"], item["name"].lower()))
    phones = _first_parent_phones([item["child_id"] for item in results])
    for item in results:
        phone, parent_name = phones.get(item["child_id"], ("", ""))
        item["parent_phone"] = phone
        item["parent_name"] = parent_name
    return results


def _first_parent_phones(child_ids: list[int]) -> dict[int, tuple[str, str]]:
    """The first linked parent's number, in guardian order."""
    phones: dict[int, tuple[str, str]] = {}
    if not child_ids:
        return phones
    links = (
        ChildGuardian.objects.filter(child_id__in=child_ids)
        .select_related("parent")
        .order_by("relationship", "parent__last_name", "pk")
    )
    for link in links:
        phones.setdefault(link.child_id, (link.parent.phone_primary, link.parent.full_name))
    return phones


def streak_for_child(child: Child, as_of: date) -> int:
    cutoff = latest_sabbath_on_or_before(as_of)
    records = child.attendance_records.filter(date__lte=cutoff).values_list("date", "status")
    return consecutive_absence_weeks(records, cutoff=cutoff)
