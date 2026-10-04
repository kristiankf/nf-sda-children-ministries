import csv

from django.http import HttpResponse
from django.shortcuts import render

from apps.children.birthdays import (
    birthdays_in_month,
    birthdays_this_week,
    birthdays_today,
    upcoming_birthdays,
)
from apps.children.groups import attach_ministry_groups, load_bands
from apps.children.models import Child
from apps.children.queries import filtered_children
from apps.core import dates
from apps.core.auth import ministry_permission_required
from apps.core.phones import format_phone
from apps.schools.levels import ClassLevel


def _child_rows(params, today):
    return filtered_children(params, today)


def _filter_query(params, **changes):
    query = params.copy()
    for key, value in changes.items():
        if value in (None, "") or query.get(key) == str(value):
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()


def _band_rows(children, bands, attr, param, params):
    rows = []
    for band in bands:
        count = sum(
            1 for child in children if getattr(child, attr) and getattr(child, attr).pk == band.pk
        )
        rows.append(
            {
                "label": band.name,
                "count": count,
                "color": band.color,
                "query": _filter_query(params, **{param: band.slug}),
                "selected": params.get(param) == band.slug,
            }
        )
    return rows


def _choice_rows(children, choices, attr, param, params):
    rows = []
    for value, label in choices:
        count = sum(1 for child in children if getattr(child, attr) == value)
        rows.append(
            {
                "label": label,
                "count": count,
                "query": _filter_query(params, **{param: value}),
                "selected": params.get(param) == value,
            }
        )
    return rows


def _class_rows(children, params):
    rows = []
    for value, label in ClassLevel.choices:
        count = sum(1 for child in children if child.class_level == value)
        if not count:
            continue
        rows.append(
            {
                "label": label,
                "count": count,
                "query": _filter_query(params, class_level=value),
                "selected": params.get("class_level") == value,
            }
        )
    without_class = sum(1 for child in children if not child.class_level)
    if without_class:
        rows.append(
            {
                "label": "No class",
                "count": without_class,
                "query": _filter_query(params, class_level="none"),
                "selected": params.get("class_level") == "none",
            }
        )
    return rows


@ministry_permission_required("children.view_child")
def children_report(request):
    today = dates.local_today()
    children = attach_ministry_groups(list(_child_rows(request.GET, today)), today)
    sabbath_bands, youth_bands = load_bands()
    return render(
        request,
        "reports/children.html",
        {
            "total": len(children),
            "sabbath_rows": _band_rows(
                children, sabbath_bands, "sabbath_class", "division", request.GET
            ),
            "youth_rows": _band_rows(children, youth_bands, "youth_group", "youth", request.GET),
            "no_sabbath": sum(1 for child in children if child.sabbath_class is None),
            "no_youth": sum(1 for child in children if child.youth_group is None),
            "no_youth_query": _filter_query(request.GET, youth="none"),
            "no_sabbath_query": _filter_query(request.GET, division="none"),
            "gender_rows": _choice_rows(
                children, Child.Gender.choices, "gender", "gender", request.GET
            ),
            "class_rows": _class_rows(children, request.GET),
            "class_levels": ClassLevel.choices,
            "sabbath_classes": sabbath_bands,
            "youth_groups": youth_bands,
            "genders": Child.Gender.choices,
            "statuses": Child.Status.choices,
            "today": today,
        },
    )


@ministry_permission_required("children.view_child")
def children_csv(request):
    today = dates.local_today()
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="children.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(
        [
            "Child",
            "Preferred name",
            "Age",
            "Date of birth",
            "Gender",
            "Status",
            "Phone",
            "Sabbath class",
            "Youth group",
            "School",
            "Class",
            "Relationship",
            "Parent or guardian",
            "Phone",
        ]
    )
    children = attach_ministry_groups(
        _child_rows(request.GET, today).prefetch_related("guardians__parent"),
        today,
    )
    for child in children:
        guardians = list(child.guardians.all())
        school = child.school_name
        class_name = child.get_class_level_display() if child.class_level else ""
        base = [
            child.full_name,
            child.preferred_name,
            child.age,
            child.date_of_birth.isoformat(),
            child.get_gender_display(),
            child.get_status_display(),
            format_phone(child.phone),
            child.sabbath_class.name if child.sabbath_class else "",
            child.youth_group.name if child.youth_group else "",
            school,
            class_name,
        ]
        if not guardians:
            writer.writerow([*base, "", "", ""])
            continue
        for link in guardians:
            writer.writerow(
                [
                    *base,
                    link.get_relationship_display(),
                    link.parent.full_name,
                    format_phone(link.parent.phone_primary),
                ]
            )
    return response


def _birthday_rows(today, scope: str):
    if scope == "today":
        return birthdays_today(today)
    if scope == "week":
        return birthdays_this_week(today)
    if scope == "month":
        return birthdays_in_month(today)
    return upcoming_birthdays(today, within_days=60)


@ministry_permission_required("children.view_child")
def birthday_report(request):
    today = dates.local_today()
    scope = request.GET.get("scope") or "upcoming"
    if scope not in {"today", "week", "month", "upcoming"}:
        scope = "upcoming"
    rows = _birthday_rows(today, scope)
    return render(
        request,
        "reports/birthdays.html",
        {"rows": rows, "scope": scope, "today": today},
    )


@ministry_permission_required("children.view_child")
def birthday_csv(request):
    today = dates.local_today()
    scope = request.GET.get("scope") or "upcoming"
    rows = _birthday_rows(
        today, scope if scope in {"today", "week", "month", "upcoming"} else "upcoming"
    )
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="birthdays.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Child", "Birthday", "Turning", "Days from today"])
    for row in rows:
        writer.writerow(
            [row["child"].short_name, row["date"].isoformat(), row["turning"], row["days"]]
        )
    return response
