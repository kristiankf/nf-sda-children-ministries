from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.attendance.models import Attendance
from apps.attendance.streaks import consecutive_absence_weeks, missing_church, streak_for_child
from apps.core.testing import link_guardian, make_child, make_parent, make_user
from apps.parents.models import ChildGuardian

ABSENT = Attendance.Status.ABSENT
PRESENT = Attendance.Status.PRESENT


class ConsecutiveAbsenceTests(TestCase):
    def test_counts_only_the_current_run_of_absences(self):
        records = [
            (date(2026, 9, 5), ABSENT),
            (date(2026, 9, 12), ABSENT),
            (date(2026, 9, 19), PRESENT),
            (date(2026, 9, 26), ABSENT),
            (date(2026, 10, 3), ABSENT),
        ]
        self.assertEqual(consecutive_absence_weeks(records, cutoff=date(2026, 10, 3)), 2)

    def test_present_breaks_the_streak(self):
        records = [
            (date(2026, 9, 19), ABSENT),
            (date(2026, 9, 26), PRESENT),
            (date(2026, 10, 3), ABSENT),
        ]
        self.assertEqual(consecutive_absence_weeks(records, cutoff=date(2026, 10, 7)), 1)

    def test_missing_records_do_not_count_as_absent(self):
        records = [
            (date(2026, 9, 12), ABSENT),
            (date(2026, 9, 26), ABSENT),
        ]
        self.assertEqual(consecutive_absence_weeks(records, cutoff=date(2026, 10, 3)), 2)

    def test_unrecorded_current_sabbath_is_not_an_absence(self):
        child = make_child()
        Attendance.objects.create(child=child, date=date(2026, 9, 26), status=PRESENT)
        Attendance.objects.create(child=child, date=date(2026, 10, 3), status=ABSENT)
        self.assertEqual(streak_for_child(child, date(2026, 10, 10)), 1)

    def test_future_absence_does_not_count_before_that_sabbath(self):
        records = [
            (date(2026, 10, 3), ABSENT),
            (date(2026, 10, 10), ABSENT),
        ]
        self.assertEqual(consecutive_absence_weeks(records, cutoff=date(2026, 10, 4)), 1)

    def test_non_saturday_absence_does_not_count(self):
        records = [
            (date(2026, 10, 3), ABSENT),
            (date(2026, 10, 5), ABSENT),
        ]
        self.assertEqual(consecutive_absence_weeks(records, cutoff=date(2026, 10, 5)), 1)

    def test_no_records_means_zero_weeks(self):
        child = make_child(first="Kojo", last="Asare")
        self.assertEqual(streak_for_child(child, date(2026, 10, 3)), 0)
        self.assertEqual(missing_church(date(2026, 10, 3), minimum=1), [])

    def test_missing_church_call_uses_the_first_parent(self):
        child = make_child(first="Kojo", last="Asare")
        mother = make_parent(first="Ama", phone="+233244111222")
        father = make_parent(first="Kofi", last="Asare", phone="+233244111223")
        link_guardian(child, mother, ChildGuardian.Relationship.MOTHER)
        link_guardian(child, father, ChildGuardian.Relationship.FATHER)
        Attendance.objects.create(child=child, date=date(2026, 10, 3), status=ABSENT)
        rows = missing_church(date(2026, 10, 3), minimum=1)
        self.assertEqual(rows[0]["parent_phone"], "+233244111223")
        self.assertEqual(rows[0]["parent_name"], "Kofi Asare")

        teacher = make_user("teacher", "TEACHER")
        self.client.force_login(teacher)
        response = self.client.get(reverse("attendance:missing"))
        self.assertContains(response, 'href="tel:+233244111223"')
