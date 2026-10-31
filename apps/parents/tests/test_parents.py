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

    def test_parent_phone_must_be_unique(self):
        make_parent(phone="+233244111222")
        response = self.client.post(
            reverse("parents:create"),
            {
                "first_name": "Other",
                "last_name": "Person",
                "phone_primary": "024 411 1222",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already used")
        self.assertFalse(Parent.objects.filter(first_name="Other").exists())

    def test_teacher_can_add_a_parent(self):
        teacher = make_user("teacher", "TEACHER")
        self.client.force_login(teacher)
        response = self.client.post(
            reverse("parents:create"),
            {"first_name": "Jane", "last_name": "Mensah", "phone_primary": "0244111222"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Parent.objects.filter(first_name="Jane", last_name="Mensah").exists())

    def test_link_several_children_from_parent_page(self):
        parent = make_parent()
        first = make_child(first="Ama")
        second = make_child(first="Kwame", last="Boateng")
        response = self.client.post(
            reverse("parents:link_children", args=[parent.pk]),
            {
                "children": [first.pk, second.pk],
                "relationship": ChildGuardian.Relationship.MOTHER,
            },
        )
        self.assertRedirects(response, parent.get_absolute_url())
        self.assertEqual(parent.child_links.count(), 2)
        self.assertTrue(
            ChildGuardian.objects.filter(
                parent=parent, child=first, relationship=ChildGuardian.Relationship.MOTHER
            ).exists()
        )
        self.assertTrue(
            ChildGuardian.objects.filter(
                parent=parent, child=second, relationship=ChildGuardian.Relationship.MOTHER
            ).exists()
        )

    def test_link_children_skips_already_linked(self):
        parent = make_parent()
        child = make_child()
        link_guardian(child, parent, ChildGuardian.Relationship.MOTHER)
        other = make_child(first="Kwame", last="Boateng")
        response = self.client.post(
            reverse("parents:link_children", args=[parent.pk]),
            {
                "children": [child.pk, other.pk],
                "relationship": ChildGuardian.Relationship.GUARDIAN,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parent.child_links.count(), 1)
        self.assertFalse(ChildGuardian.objects.filter(parent=parent, child=other).exists())

    def test_teacher_can_link_children(self):
        parent = make_parent()
        child = make_child()
        teacher = make_user("teacher", "TEACHER")
        self.client.force_login(teacher)
        response = self.client.post(
            reverse("parents:link_children", args=[parent.pk]),
            {
                "children": [child.pk],
                "relationship": ChildGuardian.Relationship.GUARDIAN,
            },
        )
        self.assertRedirects(response, parent.get_absolute_url())
        self.assertEqual(parent.child_links.count(), 1)
