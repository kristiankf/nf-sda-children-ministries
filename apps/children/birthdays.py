from datetime import date

from apps.children.models import Child
from apps.core.dates import age_in_years, days_until_birthday, next_birthday, observed_birthday


def _active_children():
    return Child.objects.filter(status=Child.Status.ACTIVE).only(
        "id",
        "first_name",
        "last_name",
        "preferred_name",
        "date_of_birth",
    )


def _upcoming_rows(children, today: date, within_days: int) -> list[dict]:
    rows = []
    for child in children:
        days = days_until_birthday(child.date_of_birth, today)
        if days > within_days:
            continue
        birthday = next_birthday(child.date_of_birth, today)
        rows.append(
            {
                "child": child,
                "date": birthday,
                "days": days,
                "turning": age_in_years(child.date_of_birth, birthday),
            }
        )
    rows.sort(
        key=lambda row: (
            row["days"],
            row["child"].last_name.lower(),
            row["child"].first_name.lower(),
        )
    )
    return rows


def upcoming_birthdays(
    today: date, *, within_days: int = 30, limit: int | None = None
) -> list[dict]:
    rows = _upcoming_rows(_active_children(), today, within_days)
    if limit is not None:
        return rows[:limit]
    return rows


def birthdays_today(today: date) -> list[dict]:
    return _upcoming_rows(_active_children(), today, 0)


def birthdays_this_week(today: date) -> list[dict]:
    """Today through the next six days, seven days in all."""
    return _upcoming_rows(_active_children(), today, 6)


def birthdays_in_month(today: date) -> list[dict]:
    children = Child.objects.filter(
        status=Child.Status.ACTIVE,
        date_of_birth__month=today.month,
    ).only("id", "first_name", "last_name", "preferred_name", "date_of_birth")
    rows = []
    for child in children:
        this_year = observed_birthday(child.date_of_birth, today.year)
        rows.append(
            {
                "child": child,
                "date": this_year,
                "days": (this_year - today).days,
                "turning": age_in_years(child.date_of_birth, this_year),
            }
        )
    rows.sort(key=lambda row: (row["date"].day, row["child"].last_name.lower()))
    return rows
