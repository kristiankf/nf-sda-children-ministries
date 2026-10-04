from datetime import date

from django.conf import settings
from django.test import SimpleTestCase

from apps.attendance.calendar import latest_sabbath_on_or_before, upcoming_sabbath


class SabbathCalendarTests(SimpleTestCase):
    def test_timezone_is_accra(self):
        self.assertEqual(settings.TIME_ZONE, "Africa/Accra")
        self.assertTrue(settings.USE_TZ)

    def test_monday_defaults_to_upcoming_saturday(self):
        monday = date(2026, 10, 5)
        self.assertEqual(monday.weekday(), 0)
        self.assertEqual(upcoming_sabbath(monday), date(2026, 10, 10))

    def test_tuesday_defaults_to_upcoming_saturday(self):
        tuesday = date(2026, 10, 6)
        self.assertEqual(tuesday.weekday(), 1)
        self.assertEqual(upcoming_sabbath(tuesday), date(2026, 10, 10))

    def test_friday_defaults_to_upcoming_saturday(self):
        friday = date(2026, 10, 9)
        self.assertEqual(friday.weekday(), 4)
        self.assertEqual(upcoming_sabbath(friday), date(2026, 10, 10))

    def test_saturday_defaults_to_today(self):
        saturday = date(2026, 10, 3)
        self.assertEqual(saturday.weekday(), 5)
        self.assertEqual(upcoming_sabbath(saturday), saturday)
        self.assertEqual(latest_sabbath_on_or_before(saturday), saturday)

    def test_sunday_defaults_to_the_following_saturday(self):
        sunday = date(2026, 10, 4)
        self.assertEqual(sunday.weekday(), 6)
        self.assertEqual(upcoming_sabbath(sunday), date(2026, 10, 10))
        self.assertEqual(latest_sabbath_on_or_before(sunday), date(2026, 10, 3))

    def test_month_boundary(self):
        friday = date(2026, 10, 30)
        self.assertEqual(friday.weekday(), 4)
        self.assertEqual(upcoming_sabbath(friday), date(2026, 10, 31))
        self.assertEqual(date(2026, 10, 31).weekday(), 5)
        self.assertEqual(latest_sabbath_on_or_before(date(2026, 11, 1)), date(2026, 10, 31))

    def test_year_boundary(self):
        friday = date(2027, 1, 1)
        sunday = date(2026, 12, 27)
        self.assertEqual(friday.weekday(), 4)
        self.assertEqual(sunday.weekday(), 6)
        self.assertEqual(upcoming_sabbath(friday), date(2027, 1, 2))
        self.assertEqual(upcoming_sabbath(sunday), date(2027, 1, 2))
        self.assertEqual(latest_sabbath_on_or_before(friday), date(2026, 12, 26))

    def test_leap_year_does_not_break_sabbath_dates(self):
        leap_day = date(2024, 2, 29)
        self.assertEqual(leap_day.weekday(), 3)
        self.assertEqual(upcoming_sabbath(leap_day), date(2024, 3, 2))
        self.assertEqual(latest_sabbath_on_or_before(date(2024, 3, 1)), date(2024, 2, 24))
        self.assertEqual(upcoming_sabbath(date(2028, 2, 29)), date(2028, 3, 4))
