from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.children.models import Child
from apps.core import dates
from apps.core.testing import make_child, make_user


class ChildrenReportTests(TestCase):
    def test_totals_follow_sabbath_class_and_gender_filters(self):
        teacher = make_user("teacher", "TEACHER")
        today = dates.local_today()
        make_child(
            "Ama",
            "Mensah",
            date_of_birth=date(today.year - 8, 1, 1),
            gender=Child.Gender.FEMALE,
        )
        make_child(
            "Kojo",
            "Asare",
            date_of_birth=date(today.year - 6, 1, 1),
            gender=Child.Gender.MALE,
        )
        self.client.force_login(teacher)

        response = self.client.get(reverse("report_children"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 2)
        sabbath = {row["label"]: row["count"] for row in response.context["sabbath_rows"]}
        youth = {row["label"]: row["count"] for row in response.context["youth_rows"]}
        self.assertEqual(sabbath["Primary"], 1)
        self.assertEqual(sabbath["Kindergarten"], 1)
        self.assertEqual(youth["Adventurer"], 2)
        self.assertEqual(response.context["no_youth"], 0)

        filtered = self.client.get(
            reverse("report_children"),
            {"division": "kindergarten", "gender": Child.Gender.MALE},
        )
        self.assertEqual(filtered.context["total"], 1)
        filtered_sabbath = {row["label"]: row["count"] for row in filtered.context["sabbath_rows"]}
        self.assertEqual(filtered_sabbath["Kindergarten"], 1)
        self.assertEqual(filtered_sabbath["Primary"], 0)
        self.assertContains(filtered, "Kindergarten")
