"""Accra-local dates and birthday arithmetic.

Age is always calculated. February 29 birthdays are observed on February 28
in years that are not leap years.
"""

from datetime import date, datetime

from django.utils import timezone


def local_today() -> date:
    return timezone.localdate()


def local_now() -> datetime:
    return timezone.localtime()


def greeting_for(moment: datetime) -> str:
    if moment.weekday() == 5:
        return "Happy Sabbath!!"
    hour = moment.hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def observed_birthday(dob: date, year: int) -> date:
    try:
        return date(year, dob.month, dob.day)
    except ValueError:
        return date(year, 2, 28)


def age_in_years(dob: date, on: date) -> int:
    years = on.year - dob.year
    if on < observed_birthday(dob, on.year):
        years -= 1
    return years


def next_birthday(dob: date, today: date) -> date:
    this_year = observed_birthday(dob, today.year)
    if this_year < today:
        return observed_birthday(dob, today.year + 1)
    return this_year


def days_until_birthday(dob: date, today: date) -> int:
    return (next_birthday(dob, today) - today).days


def subtract_years(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return date(day.year - years, 2, 28)


def latest_birth_date_for_age(today: date, years: int) -> date:
    """Latest date of birth for a person who is at least `years` old on `today`.

    A 29 February birthday is observed on 28 February in a non-leap year, so on
    that day the person has reached the new age.
    """
    cutoff = subtract_years(today, years)
    if today.month == 2 and today.day == 28 and not _is_leap(today.year) and _is_leap(cutoff.year):
        return date(cutoff.year, 2, 29)
    return cutoff


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
