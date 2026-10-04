from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.attendance.models import Attendance
from apps.children.groups import attach_ministry_groups
from apps.children.models import AgeGroup, Child
from apps.children.queries import filtered_children
from apps.core.testing import make_child, make_user


class MinistryGroupTests(TestCase):
    def _placed(self, dob, today):
        child = make_child(date_of_birth=dob)
        attach_ministry_groups([child], today)
        return child

    def test_birthday_chooses_the_sabbath_class_and_youth_group(self):
        today = date(2026, 10, 4)
        expected = [
            (date(2026, 4, 5), "baby-steps", None),
            (date(2025, 10, 5), "baby-steps", None),
            (date(2025, 10, 4), "beginner", None),
            (date(2022, 10, 5), "beginner", None),
            (date(2022, 10, 4), "kindergarten", "adventurer"),
            (date(2017, 10, 4), "primary", "adventurer"),
            (date(2016, 10, 4), "power-point", "pathfinder"),
            (date(2012, 10, 4), "realtime", "pathfinder"),
            (date(2011, 10, 4), "corner-stone", "pathfinder"),
            (date(2010, 10, 4), "corner-stone", None),
        ]
        for dob, sabbath, youth in expected:
            with self.subTest(dob=dob):
                child = self._placed(dob, today)
                self.assertEqual(child.sabbath_class.slug, sabbath)
                self.assertEqual(child.youth_group.slug if child.youth_group else None, youth)

    def test_leap_day_child_moves_on_the_observed_birthday(self):
        before = self._placed(date(2020, 2, 29), date(2024, 2, 28))
        self.assertEqual(before.sabbath_class.slug, "beginner")
        on_the_day = self._placed(date(2020, 2, 29), date(2024, 2, 29))
        self.assertEqual(on_the_day.sabbath_class.slug, "kindergarten")
        observed = make_child("Abena", "Leap", date_of_birth=date(2020, 2, 29))
        matched = filtered_children({"division": "kindergarten"}, date(2026, 2, 28))
        self.assertIn(observed, matched)

    def test_override_replaces_the_calculated_class(self):
        today = date(2026, 10, 4)
        primary = AgeGroup.objects.get(slug="primary")
        child = make_child("Kojo", "Asare", date_of_birth=date(2022, 10, 4))
        child.sabbath_class_override = primary
        child.save()
        attach_ministry_groups([child], today)
        self.assertEqual(child.sabbath_class.slug, "primary")
        self.assertEqual(child.calculated_sabbath_class.slug, "kindergarten")
        self.assertEqual(child.youth_group.slug, "adventurer")
        matched = filtered_children({"division": "primary"}, today)
        self.assertEqual(list(matched), [child])
        kindergarten = filtered_children({"division": "kindergarten"}, today)
        self.assertNotIn(child, kindergarten)

    def test_graduating_keeps_attendance_and_marks_the_child_inactive(self):
        coordinator = make_user("coordinator", "COORDINATOR")
        child = make_child("Esi", "Mensah", date_of_birth=date(2010, 1, 1))
        Attendance.objects.create(
            child=child,
            date=date(2026, 9, 26),
            status=Attendance.Status.PRESENT,
        )
        self.client.force_login(coordinator)
        response = self.client.post(reverse("children:graduate", args=[child.pk]))
        self.assertRedirects(response, child.get_absolute_url())
        child.refresh_from_db()
        self.assertEqual(child.status, Child.Status.INACTIVE)
        self.assertEqual(child.attendance_records.count(), 1)

    def test_teacher_cannot_graduate_a_child(self):
        teacher = make_user("teacher", "TEACHER")
        child = make_child("Esi", "Boateng", date_of_birth=date(2010, 1, 1))
        self.client.force_login(teacher)
        response = self.client.post(reverse("children:graduate", args=[child.pk]))
        self.assertEqual(response.status_code, 403)
        child.refresh_from_db()
        self.assertEqual(child.status, Child.Status.ACTIVE)

    def test_coordinator_can_rename_a_sabbath_class(self):
        coordinator = make_user("coordinator", "COORDINATOR")
        self.client.force_login(coordinator)
        kindergarten = AgeGroup.objects.get(slug="kindergarten")
        response = self.client.post(
            reverse("sabbath_class_edit", args=[kindergarten.slug]),
            {
                "name": "Kindy",
                "min_years": 4,
                "max_years": 6,
                "color": "lime",
            },
        )
        self.assertRedirects(response, reverse("sabbath_classes"))
        kindergarten.refresh_from_db()
        self.assertEqual(kindergarten.name, "Kindy")
        self.assertEqual(kindergarten.slug, "kindergarten")
        child = self._placed(date(2022, 10, 4), date(2026, 10, 4))
        self.assertEqual(child.sabbath_class.name, "Kindy")

    def test_overlapping_age_band_is_rejected(self):
        coordinator = make_user("coordinator", "COORDINATOR")
        self.client.force_login(coordinator)
        response = self.client.post(
            reverse("sabbath_class_create"),
            {
                "name": "Extra",
                "min_years": 5,
                "max_years": 8,
                "color": "rose",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "overlap")
        self.assertFalse(AgeGroup.objects.filter(slug="extra").exists())

    def test_teacher_cannot_open_sabbath_classes(self):
        teacher = make_user("teacher", "TEACHER")
        self.client.force_login(teacher)
        response = self.client.get(reverse("sabbath_classes"))
        self.assertEqual(response.status_code, 403)

    def test_a_class_used_as_an_override_cannot_be_removed(self):
        coordinator = make_user("coordinator", "COORDINATOR")
        primary = AgeGroup.objects.get(slug="primary")
        child = make_child("Ama", "Owusu", date_of_birth=date(2018, 1, 1))
        child.sabbath_class_override = primary
        child.save()
        self.client.force_login(coordinator)
        response = self.client.post(reverse("sabbath_class_remove", args=["primary"]))
        self.assertRedirects(response, reverse("sabbath_classes"))
        self.assertTrue(AgeGroup.objects.filter(slug="primary").exists())
