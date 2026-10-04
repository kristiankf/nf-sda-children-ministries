from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.roles import ROLE_COORDINATOR, ROLE_TEACHER
from apps.core.testing import make_user


class AuthTests(TestCase):
    def test_ministry_groups_exist(self):
        make_user("seed", "TEACHER")
        self.assertTrue(Group.objects.filter(name=ROLE_TEACHER).exists())
        self.assertTrue(Group.objects.filter(name=ROLE_COORDINATOR).exists())

    def test_login_and_logout(self):
        make_user("coordinator", "COORDINATOR")
        response = self.client.post(
            reverse("login"),
            {"username": "coordinator", "password": "test-pass-123"},
        )
        self.assertRedirects(response, reverse("dashboard"))
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

    def test_teacher_cannot_edit_the_academic_year(self):
        make_user("teacher", "TEACHER")
        self.client.login(username="teacher", password="test-pass-123")
        response = self.client.get(reverse("classes:year"))
        self.assertEqual(response.status_code, 403)
