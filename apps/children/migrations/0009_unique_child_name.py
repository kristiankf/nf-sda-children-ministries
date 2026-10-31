# Merge duplicate first/last name rows before the unique constraint.

from django.db import migrations


def merge_duplicate_children(apps, schema_editor):
    Child = apps.get_model("children", "Child")
    Attendance = apps.get_model("attendance", "Attendance")
    ChildGuardian = apps.get_model("parents", "ChildGuardian")
    ClassPlacement = apps.get_model("schools", "ClassPlacement")

    groups: dict[tuple[str, str], list] = {}
    for child in Child.objects.all().order_by("pk"):
        key = (child.first_name.casefold(), child.last_name.casefold())
        groups.setdefault(key, []).append(child)

    for children in groups.values():
        if len(children) < 2:
            continue
        keeper = children[0]
        for duplicate in children[1:]:
            for record in Attendance.objects.filter(child_id=duplicate.pk):
                if Attendance.objects.filter(child_id=keeper.pk, date=record.date).exists():
                    record.delete()
                else:
                    record.child_id = keeper.pk
                    record.save(update_fields=["child_id"])
            for link in ChildGuardian.objects.filter(child_id=duplicate.pk):
                if ChildGuardian.objects.filter(
                    child_id=keeper.pk, parent_id=link.parent_id
                ).exists():
                    link.delete()
                else:
                    link.child_id = keeper.pk
                    link.save(update_fields=["child_id"])
            for placement in ClassPlacement.objects.filter(child_id=duplicate.pk):
                if ClassPlacement.objects.filter(
                    child_id=keeper.pk,
                    academic_year_id=placement.academic_year_id,
                ).exists():
                    placement.delete()
                else:
                    placement.child_id = keeper.pk
                    placement.save(update_fields=["child_id"])
            duplicate.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("children", "0008_optional_date_of_birth"),
        ("attendance", "0001_initial"),
        ("parents", "0001_initial"),
        ("schools", "0004_early_years"),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_children, migrations.RunPython.noop),
    ]
