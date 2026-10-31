from datetime import date
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.attendance.models import Attendance
from apps.attendance.stats import sabbath_stats
from apps.core.testing import make_child, make_user
from apps.visitors.models import Visit, Visitor


class AttendanceViewTests(TestCase):
    def setUp(self):
        self.teacher = make_user("teacher", "TEACHER")
        self.child = make_child()
        self.client.force_login(self.teacher)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_roll_on_monday_opens_the_current_saturday(self, _today):
        response = self.client.get(reverse("attendance:roll"))
        self.assertContains(response, "2026-10-03")
        self.assertContains(response, "Current Sabbath")
        self.assertContains(response, "Sabbath attendance")

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_roll_on_saturday_opens_today(self, _today):
        response = self.client.get(reverse("attendance:roll"))
        self.assertContains(response, "2026-10-03")
        self.assertContains(response, "Current Sabbath")

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_coming_sabbath_is_not_open_yet(self, _today):
        response = self.client.get(reverse("attendance:roll"), {"date": "2026-10-10"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This Sabbath is not open yet")
        self.assertNotContains(response, "Save attendance")

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_coming_sabbath_cannot_be_saved(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-10-10", f"status_{self.child.pk}": "PRESENT"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This Sabbath is not open yet")
        self.assertFalse(
            Attendance.objects.filter(child=self.child, date=date(2026, 10, 10)).exists()
        )

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_weekday_shows_blank_warning(self, _today):
        response = self.client.get(reverse("attendance:roll"), {"date": "2026-10-06"})
        self.assertContains(response, "That date is not a Sabbath")
        self.assertNotContains(response, "Save attendance")

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_weekday_cannot_be_saved(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-10-06", f"status_{self.child.pk}": "ABSENT"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Attendance.objects.filter(child=self.child, date=date(2026, 10, 6)).exists()
        )

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_teacher_can_record_attendance_on_current_sabbath(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-10-03", f"status_{self.child.pk}": "PRESENT"},
        )
        self.assertEqual(response.status_code, 302)
        record = Attendance.objects.get(child=self.child, date=date(2026, 10, 3))
        self.assertEqual(record.status, Attendance.Status.PRESENT)
        self.assertEqual(record.recorded_by, self.teacher)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_teacher_can_still_record_current_sabbath_during_the_week(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-10-03", f"status_{self.child.pk}": "PRESENT"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Attendance.objects.filter(
                child=self.child, date=date(2026, 10, 3), status="PRESENT"
            ).exists()
        )

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_teacher_cannot_save_past_sabbath(self, _today):
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-09-26", f"status_{self.child.pk}": "ABSENT"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Attendance.objects.filter(child=self.child, date=date(2026, 9, 26)).exists()
        )

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_past_sabbath_shows_summary_for_teacher(self, _today):
        Attendance.objects.create(
            child=self.child, date=date(2026, 9, 26), status=Attendance.Status.PRESENT
        )
        visitor = Visitor.objects.create(
            first_name="Ama", last_name="Guest", gender=Visitor.Gender.FEMALE
        )
        Visit.objects.create(visitor=visitor, date=date(2026, 9, 26), reason="Family visit")
        response = self.client.get(reverse("attendance:roll"), {"date": "2026-09-26"})
        self.assertContains(response, "Past Sabbath")
        self.assertContains(response, self.child.full_name)
        self.assertContains(response, "Ama Guest")
        self.assertContains(response, "Download CSV")
        self.assertNotContains(response, "Edit attendance")
        self.assertNotContains(response, "Save attendance")

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_coordinator_can_edit_and_save_past_sabbath(self, _today):
        coordinator = make_user("coordinator", "COORDINATOR")
        self.client.force_login(coordinator)
        summary = self.client.get(reverse("attendance:roll"), {"date": "2026-09-26"})
        self.assertContains(summary, "Edit attendance")
        edit = self.client.get(reverse("attendance:roll"), {"date": "2026-09-26", "edit": "1"})
        self.assertContains(edit, "Save attendance")
        self.assertContains(edit, "Editing a past Sabbath")
        response = self.client.post(
            reverse("attendance:roll"),
            {"date": "2026-09-26", f"status_{self.child.pk}": "ABSENT"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("edit=1", response["Location"])
        record = Attendance.objects.get(child=self.child, date=date(2026, 9, 26))
        self.assertEqual(record.status, Attendance.Status.ABSENT)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 5))
    def test_past_sabbath_csv_download(self, _today):
        Attendance.objects.create(
            child=self.child, date=date(2026, 9, 26), status=Attendance.Status.PRESENT
        )
        response = self.client.get(reverse("attendance:roll_csv"), {"date": "2026-09-26"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        body = response.content.decode()
        self.assertIn("Child", body)
        self.assertIn(self.child.full_name, body)

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
        self.assertContains(response, "Current Sabbath")
