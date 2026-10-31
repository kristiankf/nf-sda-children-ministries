from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.attendance.stats import sabbath_stats
from apps.children.models import Child
from apps.core.testing import make_child, make_parent, make_user
from apps.visitors.follow_up import (
    FOLLOW_UP_THRESHOLD,
    convert_visitor_to_child,
    mark_followed_up,
    visitors_needing_follow_up,
)
from apps.visitors.models import Visit, Visitor


class VisitorModelTests(TestCase):
    def test_follow_up_after_three_visits_and_resets(self):
        visitor = Visitor.objects.create(
            first_name="Ama",
            last_name="Visitor",
            gender=Visitor.Gender.FEMALE,
        )
        for day in (date(2026, 10, 3), date(2026, 10, 10), date(2026, 10, 17)):
            Visit.objects.create(visitor=visitor, date=day, reason="Visiting family")
        self.assertTrue(visitor.needs_follow_up)
        self.assertEqual(len(visitors_needing_follow_up()), 1)

        user = make_user("teacher", "TEACHER")
        mark_followed_up(visitor, user)
        visitor.refresh_from_db()
        self.assertFalse(visitor.needs_follow_up)
        self.assertEqual(visitors_needing_follow_up(), [])

        for day in (date(2026, 10, 24), date(2026, 10, 31), date(2026, 11, 7)):
            Visit.objects.create(visitor=visitor, date=day, reason="Came again")
        visitor.refresh_from_db()
        self.assertEqual(visitor.visits_since_follow_up, FOLLOW_UP_THRESHOLD)
        self.assertTrue(visitor.needs_follow_up)

    def test_convert_creates_incomplete_child_and_keeps_visits(self):
        visitor = Visitor.objects.create(
            first_name="Kofi",
            last_name="Guest",
            gender=Visitor.Gender.MALE,
            date_of_birth=date(2015, 5, 1),
            address="New Fadama",
        )
        Visit.objects.create(visitor=visitor, date=date(2026, 10, 3), reason="First time")
        coordinator = make_user("coordinator", "COORDINATOR")
        child = convert_visitor_to_child(visitor, coordinator)
        visitor.refresh_from_db()
        self.assertEqual(visitor.child_id, child.pk)
        self.assertEqual(child.first_name, "Kofi")
        self.assertEqual(child.address, "New Fadama")
        self.assertTrue(child.is_incomplete)
        self.assertEqual(visitor.visits.count(), 1)
        self.assertFalse(visitor.needs_follow_up)
        self.assertEqual(visitors_needing_follow_up(), [])


class VisitorStatsTests(TestCase):
    def test_present_total_includes_visitors(self):
        child = make_child()
        from apps.attendance.models import Attendance

        Attendance.objects.create(child=child, date=date(2026, 10, 3), status="PRESENT")
        visitor = Visitor.objects.create(
            first_name="Efua",
            last_name="Guest",
            gender=Visitor.Gender.FEMALE,
        )
        Visit.objects.create(visitor=visitor, date=date(2026, 10, 3), reason="Friend invited")
        stats = sabbath_stats(date(2026, 10, 3))
        self.assertEqual(stats["children_present"], 1)
        self.assertEqual(stats["visitors"], 1)
        self.assertEqual(stats["present"], 2)
        self.assertEqual(stats["rate"], 100)


class VisitorViewTests(TestCase):
    def setUp(self):
        self.teacher = make_user("teacher", "TEACHER")
        self.client.force_login(self.teacher)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_teacher_can_add_visitor(self, _today):
        response = self.client.post(
            reverse("visitors:create"),
            {
                "visitor-first_name": "Abena",
                "visitor-last_name": "Sarpong",
                "visitor-date_of_birth": "",
                "visitor-gender": Visitor.Gender.FEMALE,
                "visitor-address": "Accra",
                "visit-existing_visitor": "",
                "visit-date": "2026-10-03",
                "visit-reason": "Visiting grandmother",
                "visit-came_with": "other",
                "visit-companion_name": "Akosua Mensah",
                "visit-companion_phone": "0244123456",
                "visit-brought_by_parent": "",
                "visit-brought_by_child": "",
            },
        )
        visitor = Visitor.objects.get(first_name="Abena", last_name="Sarpong")
        self.assertRedirects(response, visitor.get_absolute_url())
        visit = visitor.visits.get()
        self.assertEqual(visit.reason, "Visiting grandmother")
        self.assertEqual(visit.companion_name, "Akosua Mensah")
        self.assertEqual(visit.companion_phone, "+233244123456")

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_link_existing_parent_as_companion(self, _today):
        parent = make_parent(first="Jane", last="Mensah", phone="+233244999888")
        response = self.client.post(
            reverse("visitors:create"),
            {
                "visitor-first_name": "Yaw",
                "visitor-last_name": "Guest",
                "visitor-gender": Visitor.Gender.MALE,
                "visitor-address": "",
                "visit-existing_visitor": "",
                "visit-date": "2026-10-03",
                "visit-reason": "Came with aunt",
                "visit-came_with": "parent",
                "visit-brought_by_parent": str(parent.pk),
                "visit-brought_by_child": "",
                "visit-companion_name": "",
                "visit-companion_phone": "",
            },
        )
        visitor = Visitor.objects.get(first_name="Yaw")
        self.assertRedirects(response, visitor.get_absolute_url())
        self.assertEqual(visitor.visits.get().brought_by_parent_id, parent.pk)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_returning_visitor_adds_visit_only(self, _today):
        visitor = Visitor.objects.create(
            first_name="Ama",
            last_name="Return",
            gender=Visitor.Gender.FEMALE,
        )
        Visit.objects.create(visitor=visitor, date=date(2026, 9, 26), reason="First")
        response = self.client.post(
            reverse("visitors:create"),
            {
                "visitor-first_name": "",
                "visitor-last_name": "",
                "visitor-gender": Visitor.Gender.FEMALE,
                "visit-existing_visitor": str(visitor.pk),
                "visit-date": "2026-10-03",
                "visit-reason": "Second visit",
                "visit-came_with": "none",
                "visit-brought_by_parent": "",
                "visit-brought_by_child": "",
                "visit-companion_name": "",
                "visit-companion_phone": "",
            },
        )
        self.assertRedirects(response, visitor.get_absolute_url())
        self.assertEqual(Visitor.objects.filter(first_name="Ama", last_name="Return").count(), 1)
        self.assertEqual(visitor.visits.count(), 2)

    def test_teacher_can_convert(self):
        visitor = Visitor.objects.create(
            first_name="No",
            last_name="Convert",
            gender=Visitor.Gender.UNSPECIFIED,
        )
        response = self.client.get(reverse("visitors:convert", args=[visitor.pk]))
        self.assertEqual(response.status_code, 200)

    def test_coordinator_can_convert(self):
        coordinator = make_user("coordinator", "COORDINATOR")
        self.client.force_login(coordinator)
        visitor = Visitor.objects.create(
            first_name="Yes",
            last_name="Convert",
            gender=Visitor.Gender.FEMALE,
        )
        response = self.client.post(reverse("visitors:convert", args=[visitor.pk]))
        visitor.refresh_from_db()
        self.assertTrue(visitor.is_converted)
        self.assertRedirects(response, visitor.child.get_absolute_url())
        self.assertEqual(Child.objects.filter(pk=visitor.child_id).count(), 1)

    @patch("apps.core.dates.local_today", return_value=date(2026, 10, 3))
    def test_dashboard_shows_visitor_quick_action_and_follow_up(self, _today):
        visitor = Visitor.objects.create(
            first_name="Reach",
            last_name="Out",
            gender=Visitor.Gender.FEMALE,
        )
        for day in (date(2026, 9, 19), date(2026, 9, 26), date(2026, 10, 3)):
            Visit.objects.create(visitor=visitor, date=day, reason="Again")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Add visitor")
        self.assertContains(response, "Reach Out")
        self.assertContains(response, "Visitors to reach out to")
