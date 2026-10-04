"""Sabbath dates for Children's Ministries.

The regular ministry day is Saturday. `upcoming_sabbath` is the date the
attendance roll should open on. `latest_sabbath_on_or_before` is the latest
Saturday that can count toward absence streaks.
"""

from datetime import date, timedelta

SATURDAY = 5


def is_sabbath(day: date) -> bool:
    return day.weekday() == SATURDAY


def upcoming_sabbath(day: date) -> date:
    """Return `day` when it is Saturday, otherwise the next Saturday."""
    days_ahead = (SATURDAY - day.weekday()) % 7
    return day + timedelta(days=days_ahead)


def latest_sabbath_on_or_before(day: date) -> date:
    """Return the Saturday on or before `day`."""
    days_back = (day.weekday() - SATURDAY) % 7
    return day - timedelta(days=days_back)
