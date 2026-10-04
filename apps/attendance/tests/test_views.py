from datetime import date
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.attendance.models import Attendance
from apps.attendance.stats import sabbath_stats
from apps.core.testing import make_child, make_user


class AttendanceViewTests(TestCase):
    def setUp(self):
        self.teacher = make_user("teacher", "TEACHER")
        self.child = make_child()
        self.client.force_login(self.teacher)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_roll_on_monday_opens_the_coming_saturday(self, _today):
        response = self.client.get(reverse("attendance:roll"))
        self.assertContains(response, "2026-10-10")
        self.assertContains(response, "Sabbath attendance")

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_roll_on_saturday_opens_today(self, _today):
        response = self.client.get(reverse("attendance:roll"))
        self.assertContains(response, "2026-10-03")

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_coming_sabbath_cannot_be_saved_before_that_day(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-10-10", f"status_{self.child.pk}": "PRESENT"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot be saved until that day")
        self.assertContains(response, "This date has not arrived yet")
        self.assertNotContains(response, "Save attendance")
        self.assertFalse(
            Attendance.objects.filter(child=self.child, date=date(2026, 10, 10)).exists()
        )

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_weekday_after_today_cannot_be_saved(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-10-06", f"status_{self.child.pk}": "ABSENT"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Attendance.objects.filter(child=self.child, date=date(2026, 10, 6)).exists()
        )

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_teacher_can_record_attendance(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-10-03", f"status_{self.child.pk}": "PRESENT"},
        )
        self.assertEqual(response.status_code, 302)
        record = Attendance.objects.get(child=self.child, date=date(2026, 10, 3))
        self.assertEqual(record.status, Attendance.Status.PRESENT)
        self.assertEqual(record.recorded_by, self.teacher)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_past_sabbath_can_still_be_saved(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-09-26", f"status_{self.child.pk}": "ABSENT"},
        )
        self.assertEqual(response.status_code, 302)
        record = Attendance.objects.get(child=self.child, date=date(2026, 9, 26))
        self.assertEqual(record.status, Attendance.Status.ABSENT)

    def test_duplicate_attendance_is_rejected(self):
        Attendance.objects.create(
            child=self.child,
            date=date(2026, 10, 3),
            status=Attendance.Status.PRESENT,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Attendance.objects.create(
                    child=self.child,
                    date=date(2026, 10, 3),
                    status=Attendance.Status.ABSENT,
                )

    def test_statistics_count_present_and_absent(self):
        other = make_child(first="Kwame", last="Boateng")
        Attendance.objects.create(child=self.child, date=date(2026, 10, 3), status="PRESENT")
        Attendance.objects.create(child=other, date=date(2026, 10, 3), status="ABSENT")
        stats = sabbath_stats(date(2026, 10, 3))
        self.assertEqual(stats["present"], 1)
        self.assertEqual(stats["absent"], 1)
        self.assertEqual(stats["rate"], 50)

    def test_anonymous_user_cannot_open_attendance(self):
        self.client.logout()
        response = self.client.get(reverse("attendance:roll"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_dashboard_shows_the_current_absence_streak(self, _today):
        child = make_child(first="Sarah", last="Owusu", preferred_name="")
        for absent_on in (date(2026, 9, 19), date(2026, 9, 26), date(2026, 10, 3)):
            Attendance.objects.create(child=child, date=absent_on, status=Attendance.Status.ABSENT)
        Attendance.objects.create(
            child=child, date=date(2026, 9, 12), status=Attendance.Status.PRESENT
        )
        coordinator = make_user("coordinator", "COORDINATOR")
        self.client.force_login(coordinator)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Sarah Owusu")
        self.assertContains(response, "3 weeks")
        self.assertContains(response, "This Sabbath")
