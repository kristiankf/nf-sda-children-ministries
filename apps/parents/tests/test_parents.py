from django.test import TestCase
from django.urls import reverse

from apps.core.testing import link_guardian, make_child, make_parent, make_user
from apps.parents.models import ChildGuardian, Parent


class ParentTests(TestCase):
    def setUp(self):
        self.coordinator = make_user("coordinator", "COORDINATOR")
        self.client.force_login(self.coordinator)

    def test_create_parent_and_link_several_children(self):
        response = self.client.post(
            reverse("parents:create"),
            {
                "first_name": "Jane",
                "last_name": "Mensah",
                "phone_primary": "024 411 1222",
            },
        )
        parent = Parent.objects.get(last_name="Mensah")
        self.assertEqual(parent.phone_primary, "+233244111222")
        self.assertRedirects(response, parent.get_absolute_url())
        first = make_child(first="Ama")
        second = make_child(first="Kwame", last="Boateng")
        link_guardian(first, parent, ChildGuardian.Relationship.MOTHER)
        link_guardian(second, parent, ChildGuardian.Relationship.GUARDIAN)
        self.assertEqual(parent.child_links.count(), 2)

    def test_child_can_have_more_than_one_guardian(self):
        child = make_child()
        mother = make_parent(first="Jane", phone="+233244111222")
        father = make_parent(first="John", last="Mensah", phone="+233244111223")
        link_guardian(child, mother, ChildGuardian.Relationship.MOTHER)
        link_guardian(child, father, ChildGuardian.Relationship.FATHER)
        self.assertEqual(child.guardians.count(), 2)

    def test_invalid_phone_is_rejected(self):
        response = self.client.post(
            reverse("parents:create"),
            {"first_name": "Jane", "last_name": "Mensah", "phone_primary": "123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Parent.objects.filter(last_name="Mensah").exists())

    def test_teacher_cannot_add_a_parent(self):
        teacher = make_user("teacher", "TEACHER")
        self.client.force_login(teacher)
        response = self.client.post(
            reverse("parents:create"),
            {"first_name": "Jane", "last_name": "Mensah", "phone_primary": "0244111222"},
        )
        self.assertEqual(response.status_code, 403)
