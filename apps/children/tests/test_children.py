import tempfile
from datetime import date
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.children.forms import ChildForm
from apps.children.models import Child
from apps.children.queries import filtered_children
from apps.core.testing import link_guardian, make_child, make_parent, make_user
from apps.schools.levels import ClassLevel
from apps.schools.models import ClassPlacement


def _png() -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), "blue").save(buffer, format="PNG")
    return SimpleUploadedFile("portrait.png", buffer.getvalue(), content_type="image/png")


class ChildTests(TestCase):
    def setUp(self):
        self.coordinator = make_user("coordinator", "COORDINATOR")
        self.teacher = make_user("teacher", "TEACHER")

    def test_coordinator_can_create_and_update_a_child(self):
        self.client.force_login(self.coordinator)
        response = self.client.post(
            reverse("children:create"),
            {
                "first_name": "Ama",
                "last_name": "Mensah",
                "date_of_birth": "2016-10-14",
                "gender": "FEMALE",
                "status": "ACTIVE",
                "school_name": "Sample Harbour School",
                "class_level": ClassLevel.BASIC_4,
            },
        )
        child = Child.objects.get(first_name="Ama", last_name="Mensah")
        self.assertRedirects(response, child.get_absolute_url())
        self.assertEqual(child.created_by, self.coordinator)
        self.assertEqual(child.class_level, ClassLevel.BASIC_4)
        self.assertEqual(child.school_name, "Sample Harbour School")
        self.assertTrue(
            ClassPlacement.objects.filter(child=child, class_level=ClassLevel.BASIC_4).exists()
        )
        response = self.client.post(
            reverse("children:edit", args=[child.pk]),
            {
                "first_name": "Ama",
                "last_name": "Mensah",
                "preferred_name": "Amy",
                "date_of_birth": "2016-10-14",
                "gender": "FEMALE",
                "status": "ACTIVE",
                "school_name": "Sample Harbour School",
                "class_level": ClassLevel.BASIC_5,
            },
        )
        self.assertRedirects(response, child.get_absolute_url())
        child.refresh_from_db()
        self.assertEqual(child.preferred_name, "Amy")
        self.assertEqual(child.class_level, ClassLevel.BASIC_5)

    def test_future_date_of_birth_is_rejected(self):
        form = ChildForm(
            data={
                "first_name": "Ama",
                "last_name": "Mensah",
                "date_of_birth": "2999-01-01",
                "gender": "FEMALE",
                "status": "ACTIVE",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("date_of_birth", form.errors)

    def test_child_phone_is_optional_and_stored_as_e164(self):
        form = ChildForm(
            data={
                "first_name": "Ama",
                "last_name": "Mensah",
                "date_of_birth": "2016-10-14",
                "gender": "FEMALE",
                "status": "ACTIVE",
                "phone": "024 412 3456",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        child = form.save()
        self.assertEqual(child.phone, "+233244123456")

        empty = ChildForm(
            data={
                "first_name": "Kojo",
                "last_name": "Asare",
                "date_of_birth": "2016-10-14",
                "gender": "MALE",
                "status": "ACTIVE",
                "phone": "",
            }
        )
        self.assertTrue(empty.is_valid(), empty.errors)

        invalid = ChildForm(
            data={
                "first_name": "Esi",
                "last_name": "Boateng",
                "date_of_birth": "2016-10-14",
                "gender": "FEMALE",
                "status": "ACTIVE",
                "phone": "123",
            }
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn("phone", invalid.errors)

    def test_search_matches_name_parent_phone_and_school(self):
        child = make_child(preferred_name="Amy", school_name="Sample Harbour School")
        parent = make_parent(phone="+233244555666")
        link_guardian(child, parent)
        today = date(2026, 10, 3)
        self.assertEqual(list(filtered_children({"q": "Amy"}, today)), [child])
        self.assertEqual(list(filtered_children({"q": "0244555666"}, today)), [child])
        self.assertEqual(list(filtered_children({"q": "Harbour"}, today)), [child])
        self.assertEqual(filtered_children({"q": "Nobody"}, today).count(), 0)

    def test_teacher_cannot_create_a_child(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("children:create"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_cannot_view_a_child(self):
        child = make_child()
        response = self.client.get(child.get_absolute_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_teacher_can_view_a_child_but_not_the_photo_without_a_record(self):
        child = make_child()
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(child.get_absolute_url()).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("children:photo", args=[child.pk])).status_code, 404
        )

    def test_photo_requires_a_real_image_and_login(self):
        self.client.force_login(self.coordinator)
        media_root = tempfile.mkdtemp()
        with override_settings(MEDIA_ROOT=media_root):
            self._assert_photo_rules()

    def _assert_photo_rules(self):
        self.client.force_login(self.coordinator)
        response = self.client.post(
            reverse("children:create"),
            {
                "first_name": "Ama",
                "last_name": "Photo",
                "date_of_birth": "2016-10-14",
                "gender": "FEMALE",
                "status": "ACTIVE",
                "photo": SimpleUploadedFile(
                    "notes.txt", b"not an image", content_type="text/plain"
                ),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Child.objects.filter(last_name="Photo").exists())

        response = self.client.post(
            reverse("children:create"),
            {
                "first_name": "Ama",
                "last_name": "Photo",
                "date_of_birth": "2016-10-14",
                "gender": "FEMALE",
                "status": "ACTIVE",
                "photo": _png(),
            },
        )
        child = Child.objects.get(last_name="Photo")
        self.assertRedirects(response, child.get_absolute_url())
        self.client.logout()
        photo = self.client.get(reverse("children:photo", args=[child.pk]))
        self.assertEqual(photo.status_code, 302)
