from datetime import date

from django.test import TestCase

from apps.children.birthdays import birthdays_in_month, birthdays_today, upcoming_birthdays
from apps.core.dates import age_in_years, next_birthday
from apps.core.testing import make_child


class BirthdayCalculationTests(TestCase):
    def test_age_is_calculated_from_the_date_of_birth(self):
        self.assertEqual(age_in_years(date(2016, 10, 14), date(2026, 10, 13)), 9)
        self.assertEqual(age_in_years(date(2016, 10, 14), date(2026, 10, 14)), 10)

    def test_leap_day_birthday_is_observed_on_28_february(self):
        dob = date(2020, 2, 29)
        self.assertEqual(age_in_years(dob, date(2026, 2, 27)), 5)
        self.assertEqual(age_in_years(dob, date(2026, 2, 28)), 6)
        self.assertEqual(next_birthday(dob, date(2026, 2, 28)), date(2026, 2, 28))
        self.assertEqual(age_in_years(dob, date(2024, 2, 29)), 4)
        self.assertEqual(next_birthday(dob, date(2024, 3, 1)), date(2025, 2, 28))

    def test_upcoming_birthdays_and_month_filter(self):
        today = date(2026, 10, 3)
        today_child = make_child(first="Efua", last="Darko", date_of_birth=date(2017, 10, 3))
        soon = make_child(first="Kojo", last="Asare", date_of_birth=date(2019, 10, 10))
        make_child(first="Adwoa", last="Quaye", date_of_birth=date(2018, 11, 2))

        names = [row["child"].pk for row in upcoming_birthdays(today, within_days=14)]
        self.assertIn(today_child.pk, names)
        self.assertIn(soon.pk, names)
        self.assertEqual(birthdays_today(today)[0]["child"].pk, today_child.pk)

        month_names = [row["child"].first_name for row in birthdays_in_month(today)]
        self.assertEqual(month_names, ["Efua", "Kojo"])
        self.assertNotIn("Adwoa", month_names)
