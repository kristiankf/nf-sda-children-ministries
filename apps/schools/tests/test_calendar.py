from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.core.dates import local_today
from apps.core.testing import make_child, make_user
from apps.schools.calendar import advance_academic_calendar, period_after, period_containing
from apps.schools.levels import ClassLevel
from apps.schools.models import AcademicYear, ClassPlacement


class AcademicPeriodTests(SimpleTestCase):
    def test_october_belongs_to_the_september_year(self):
        start, end, name = period_containing(date(2026, 10, 4))
        self.assertEqual(start, date(2026, 9, 1))
        self.assertEqual(end, date(2027, 8, 31))
        self.assertEqual(name, "2026/2027")

    def test_march_belongs_to_the_previous_september(self):
        start, end, name = period_containing(date(2027, 3, 1))
        self.assertEqual(start, date(2026, 9, 1))
        self.assertEqual(end, date(2027, 8, 31))
        self.assertEqual(name, "2026/2027")

    def test_the_next_year_starts_the_day_after_this_one_ends(self):
        start, end, name = period_after(date(2027, 8, 31))
        self.assertEqual(start, date(2027, 9, 1))
        self.assertEqual(end, date(2028, 8, 31))
        self.assertEqual(name, "2027/2028")


class ClassProgressionTests(TestCase):
    def test_an_open_year_leaves_the_class_where_it_is(self):
        child = make_child(class_level=ClassLevel.BASIC_5)
        advance_academic_calendar(local_today())
        child.refresh_from_db()
        self.assertEqual(child.class_level, ClassLevel.BASIC_5)

    def test_an_active_child_moves_up_when_the_year_ends(self):
        child = make_child(class_level=ClassLevel.BASIC_5)
        closed = AcademicYear.objects.get(is_current=True)
        closed.end_date = date(2027, 8, 31)
        closed.save(update_fields=["end_date", "updated_at"])

        current = advance_academic_calendar(date(2027, 9, 1))

        child.refresh_from_db()
        self.assertEqual(child.class_level, ClassLevel.BASIC_6)
        self.assertEqual(current.start_date, date(2027, 9, 1))
        self.assertEqual(current.end_date, date(2028, 8, 31))
        self.assertEqual(
            ClassPlacement.objects.get(child=child, academic_year=closed).class_level,
            ClassLevel.BASIC_5,
        )
        self.assertEqual(
            ClassPlacement.objects.get(child=child, academic_year=current).class_level,
            ClassLevel.BASIC_6,
        )

    def test_shs_3_stays_in_shs_3(self):
        child = make_child(class_level=ClassLevel.SHS_3)
        self._close_current_year(date(2027, 8, 31))
        current = advance_academic_calendar(date(2027, 9, 1))
        child.refresh_from_db()
        self.assertEqual(child.class_level, ClassLevel.SHS_3)
        self.assertEqual(
            ClassPlacement.objects.get(child=child, academic_year=current).class_level,
            ClassLevel.SHS_3,
        )

    def test_an_inactive_child_stays_in_the_same_class(self):
        child = make_child(class_level=ClassLevel.BASIC_5)
        child.status = child.Status.INACTIVE
        child.save(update_fields=["status", "updated_at"])
        self._close_current_year(date(2027, 8, 31))
        current = advance_academic_calendar(date(2027, 9, 1))
        child.refresh_from_db()
        self.assertEqual(child.class_level, ClassLevel.BASIC_5)
        self.assertFalse(ClassPlacement.objects.filter(child=child, academic_year=current).exists())

    def test_a_child_without_a_class_is_left_unplaced(self):
        child = make_child(class_level="", school_name="")
        self._close_current_year(date(2027, 8, 31))
        advance_academic_calendar(date(2027, 9, 1))
        child.refresh_from_db()
        self.assertEqual(child.class_level, "")
        self.assertFalse(ClassPlacement.objects.filter(child=child).exists())

    def test_missed_years_each_move_the_class_one_step(self):
        child = make_child(class_level=ClassLevel.BASIC_5)
        year = AcademicYear.objects.get(is_current=True)
        year.name = "2024/2025"
        year.start_date = date(2024, 9, 1)
        year.end_date = date(2025, 8, 31)
        year.save(update_fields=["name", "start_date", "end_date", "updated_at"])

        current = advance_academic_calendar(date(2026, 10, 4))

        child.refresh_from_db()
        self.assertEqual(child.class_level, ClassLevel.JHS_1)
        self.assertEqual(current.name, "2026/2027")
        placed = {
            placement.academic_year.name: placement.class_level
            for placement in ClassPlacement.objects.filter(child=child)
        }
        self.assertEqual(
            placed,
            {
                "2024/2025": ClassLevel.BASIC_5,
                "2025/2026": ClassLevel.BASIC_6,
                "2026/2027": ClassLevel.JHS_1,
            },
        )

    def test_a_signed_in_page_moves_the_class_after_the_end_date(self):
        teacher = make_user("teacher", "TEACHER")
        child = make_child(class_level=ClassLevel.BASIC_5)
        self.client.force_login(teacher)
        with patch("apps.schools.calendar.local_today", return_value=date(2027, 9, 1)):
            response = self.client.get(reverse("classes:list"))
        child.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(child.class_level, ClassLevel.BASIC_6)
        levels = {row["label"]: row["count"] for row in response.context["levels"]}
        self.assertEqual(levels["Basic 6"], 1)
        self.assertEqual(levels["Basic 5"], 0)
        self.assertContains(response, "2027/2028")

    def test_a_coordinator_can_change_the_year_dates(self):
        coordinator = make_user("coordinator", "COORDINATOR")
        self.client.force_login(coordinator)
        self.client.get(reverse("classes:year"))
        year = AcademicYear.objects.get(is_current=True)
        today = local_today()
        posted_end = today if today < year.end_date else year.end_date
        response = self.client.post(
            reverse("classes:year"),
            {
                "start_date": year.start_date.isoformat(),
                "end_date": posted_end.isoformat(),
            },
        )
        self.assertRedirects(response, reverse("classes:list"))
        year.refresh_from_db()
        self.assertEqual(year.end_date, posted_end)
        self.assertTrue(year.is_current)

    def test_a_teacher_can_open_the_class_list(self):
        teacher = make_user("teacher", "TEACHER")
        make_child(class_level=ClassLevel.BASIC_1)
        self.client.force_login(teacher)
        response = self.client.get(reverse("classes:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pre-school")
        self.assertContains(response, "Basic 1")
        self.assertNotContains(response, "Edit dates")

    def _close_current_year(self, end):
        year = AcademicYear.objects.get(is_current=True)
        year.end_date = end
        year.save(update_fields=["end_date", "updated_at"])
        return year
