from datetime import date

from django.contrib.auth.models import Group, User

from apps.accounts.roles import ensure_ministry_roles
from apps.children.models import Child
from apps.parents.models import ChildGuardian, Parent
from apps.schools.levels import ClassLevel


def make_user(username: str, role: str) -> User:
    ensure_ministry_roles()
    user = User.objects.create_user(username=username, password="test-pass-123")
    if role == "ADMIN":
        user.is_staff = True
        user.is_superuser = True
    elif role == "COORDINATOR":
        user.is_staff = True
    user.save()
    user.groups.add(Group.objects.get(name=role))
    return user


def make_child(first: str = "Ama", last: str = "Mensah", **kwargs) -> Child:
    defaults = {
        "date_of_birth": date(2016, 10, 14),
        "gender": Child.Gender.FEMALE,
        "status": Child.Status.ACTIVE,
        "school_name": "Sample Harbour School",
        "class_level": ClassLevel.BASIC_4,
    }
    defaults.update(kwargs)
    return Child.objects.create(first_name=first, last_name=last, **defaults)


def make_parent(first: str = "Jane", last: str = "Mensah", phone: str = "+233244111222") -> Parent:
    return Parent.objects.create(first_name=first, last_name=last, phone_primary=phone)


def link_guardian(child, parent, relationship=ChildGuardian.Relationship.MOTHER) -> ChildGuardian:
    return ChildGuardian.objects.create(child=child, parent=parent, relationship=relationship)
