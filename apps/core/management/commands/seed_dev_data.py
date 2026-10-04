"""Fictional sample data for local development. Never uses real children."""

from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.roles import ROLE_ADMIN, ROLE_COORDINATOR, ROLE_TEACHER, ensure_ministry_roles
from apps.attendance.calendar import latest_sabbath_on_or_before
from apps.attendance.models import Attendance
from apps.children.models import Child
from apps.core.dates import local_today
from apps.parents.models import ChildGuardian, Parent
from apps.schools.levels import ClassLevel
from apps.schools.models import AcademicYear

DEV_PASSWORD = "dev-only-change-me"
FICTIONAL = "Fictional demonstration record. Not a real child."


class Command(BaseCommand):
    help = "Load fictional development records for New Fadama SDA Children's Ministries."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_dev_data only runs when DEBUG is on.")
        ensure_ministry_roles()
        with transaction.atomic():
            self._users()
            self._records()
        self.stdout.write(self.style.SUCCESS("Sample data is ready."))
        self.stdout.write("Development sign-in (change these before any real deployment):")
        self.stdout.write(f"  admin / {DEV_PASSWORD}")
        self.stdout.write(f"  coordinator / {DEV_PASSWORD}")
        self.stdout.write(f"  teacher / {DEV_PASSWORD}")

    def _users(self) -> None:
        specs = [
            ("admin", ROLE_ADMIN, True, True),
            ("coordinator", ROLE_COORDINATOR, True, False),
            ("teacher", ROLE_TEACHER, False, False),
        ]
        for username, role, is_staff, is_superuser in specs:
            user, _created = User.objects.get_or_create(
                username=username,
                defaults={"is_staff": is_staff, "is_superuser": is_superuser},
            )
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.set_password(DEV_PASSWORD)
            user.save()
            user.groups.set([Group.objects.get(name=role)])

    def _records(self) -> None:
        today = local_today()
        start_year = today.year if today.month >= 9 else today.year - 1
        year_name = f"{start_year}/{start_year + 1}"
        year, _created = AcademicYear.objects.get_or_create(
            name=year_name,
            defaults={
                "start_date": date(start_year, 9, 1),
                "end_date": date(start_year + 1, 8, 31),
                "is_current": True,
            },
        )
        AcademicYear.objects.filter(is_current=True).exclude(pk=year.pk).update(is_current=False)
        year.start_date = date(start_year, 9, 1)
        year.end_date = date(start_year + 1, 8, 31)
        year.is_current = True
        year.save()

        harbour = "Sample Harbour Basic School"
        court = "Sample Court JHS"
        lakeside = "Sample Lakeside SHS"

        jane = self._parent("Jane", "Mensah", "+233244100001")
        john = self._parent("John", "Mensah", "+233244100002")
        grace = self._parent("Grace", "Owusu", "+233244100003")
        samuel = self._parent("Samuel", "Addo", "+233244100004")
        abena = self._parent("Abena", "Mensah", "+233244100005")
        kwesi = self._parent("Kwesi", "Boateng", "+233244100006")

        ama = self._child(
            "Ama",
            "Mensah",
            self._dob(today, 14, 10),
            Child.Gender.FEMALE,
            harbour,
            ClassLevel.BASIC_4,
        )
        kwame = self._child(
            "Kwame",
            "Boateng",
            self._dob(today, 40, 9),
            Child.Gender.MALE,
            harbour,
            ClassLevel.BASIC_2,
        )
        sarah = self._child(
            "Sarah",
            "Owusu",
            self._dob(today, 3, 11),
            Child.Gender.FEMALE,
            harbour,
            ClassLevel.BASIC_6,
        )
        daniel = self._child(
            "Daniel",
            "Addo",
            self._dob(today, 10, 8),
            Child.Gender.MALE,
            court,
            ClassLevel.JHS_1,
        )
        michael = self._child(
            "Michael",
            "Mensah",
            self._dob(today, 21, 12),
            Child.Gender.MALE,
            court,
            ClassLevel.JHS_2,
        )
        efua = self._child(
            "Efua",
            "Darko",
            self._birthday_dob(today, 0, 9),
            Child.Gender.FEMALE,
            harbour,
            ClassLevel.BASIC_4,
        )
        kojo = self._child(
            "Kojo",
            "Asare",
            self._birthday_dob(today, 3, 7),
            Child.Gender.MALE,
            lakeside,
            ClassLevel.SHS_1,
        )
        adwoa = self._child(
            "Adwoa",
            "Quaye",
            self._birthday_dob(today, 12, 6),
            Child.Gender.FEMALE,
            harbour,
            ClassLevel.BASIC_2,
        )

        self._link(ama, jane, ChildGuardian.Relationship.MOTHER)
        self._link(ama, john, ChildGuardian.Relationship.FATHER)
        self._link(kwame, jane, ChildGuardian.Relationship.MOTHER)
        self._link(kwame, kwesi, ChildGuardian.Relationship.FATHER)
        self._link(sarah, grace, ChildGuardian.Relationship.MOTHER)
        self._link(daniel, samuel, ChildGuardian.Relationship.FATHER)
        self._link(michael, abena, ChildGuardian.Relationship.MOTHER)
        self._link(efua, grace, ChildGuardian.Relationship.GUARDIAN)
        self._link(kojo, samuel, ChildGuardian.Relationship.GUARDIAN)
        self._link(adwoa, abena, ChildGuardian.Relationship.MOTHER)

        current = latest_sabbath_on_or_before(today)
        sabbaths = [current - timedelta(days=7 * offset) for offset in range(5, -1, -1)]
        present = Attendance.Status.PRESENT
        absent = Attendance.Status.ABSENT
        patterns = {
            ama: [present, present, present, present, present, present],
            kwame: [present, absent, present, present, absent, present],
            sarah: [present, present, present, absent, absent, absent],
            daniel: [present, present, present, present, absent, absent],
            michael: [present, present, present, present, absent, absent],
            efua: [present, present, absent, present, present, present],
            adwoa: [present, present, present, present, present, absent],
        }
        # Kojo missed a recorded Sabbath in the middle, then was absent again.
        kojo_pattern = {
            sabbaths[1]: absent,
            sabbaths[3]: absent,
            sabbaths[5]: absent,
        }
        for child, pattern in patterns.items():
            for sabbath, status in zip(sabbaths, pattern, strict=True):
                self._mark(child, sabbath, status)
        for sabbath, status in kojo_pattern.items():
            self._mark(kojo, sabbath, status)

    def _parent(self, first, last, phone):
        parent, _created = Parent.objects.get_or_create(
            first_name=first,
            last_name=last,
            phone_primary=phone,
            defaults={"notes": "Fictional sample parent."},
        )
        return parent

    def _child(self, first, last, dob, gender, school_name, class_level):
        child, _created = Child.objects.get_or_create(
            first_name=first,
            last_name=last,
            date_of_birth=dob,
            defaults={
                "gender": gender,
                "school_name": school_name,
                "class_level": class_level,
                "status": Child.Status.ACTIVE,
                "notes": FICTIONAL,
            },
        )
        child.gender = gender
        child.school_name = school_name
        child.class_level = class_level
        child.save()
        return child

    def _link(self, child, parent, relationship):
        ChildGuardian.objects.get_or_create(
            child=child,
            parent=parent,
            defaults={"relationship": relationship},
        )

    def _mark(self, child, sabbath, status):
        Attendance.objects.update_or_create(
            child=child,
            date=sabbath,
            defaults={"status": status},
        )

    def _dob(self, today, day, month):
        year = today.year - 10
        try:
            born = date(year, month, day)
        except ValueError:
            born = date(year, month, 28)
        if born > today:
            born = born.replace(year=year - 1)
        return born

    def _birthday_dob(self, today, days_ahead, age):
        birthday = today + timedelta(days=days_ahead)
        year = birthday.year - age
        try:
            return date(year, birthday.month, birthday.day)
        except ValueError:
            return date(year, 2, 28)
