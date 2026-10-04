from django.db import migrations


def _match_level(name: str) -> str:
    key = " ".join((name or "").lower().replace("-", " ").split())
    aliases = {
        "pre school": "PRESCHOOL",
        "preschool": "PRESCHOOL",
        "nursery": "PRESCHOOL",
        "kg": "PRESCHOOL",
        "kindergarten": "PRESCHOOL",
    }
    for number in range(1, 7):
        aliases[f"class {number}"] = f"BASIC_{number}"
        aliases[f"basic {number}"] = f"BASIC_{number}"
        aliases[f"primary {number}"] = f"BASIC_{number}"
    for number in range(1, 4):
        aliases[f"jhs {number}"] = f"JHS_{number}"
        aliases[f"jhs{number}"] = f"JHS_{number}"
        aliases[f"shs {number}"] = f"SHS_{number}"
        aliases[f"shs{number}"] = f"SHS_{number}"
    return aliases.get(key, "")


def copy_school_and_class(apps, schema_editor):
    Child = apps.get_model("children", "Child")
    School = apps.get_model("schools", "School")
    SchoolClass = apps.get_model("schools", "SchoolClass")
    ClassPlacement = apps.get_model("schools", "ClassPlacement")
    AcademicYear = apps.get_model("schools", "AcademicYear")

    schools = {row.id: row.name for row in School.objects.all()}
    classes = {row.id: row for row in SchoolClass.objects.all()}
    year = AcademicYear.objects.filter(is_current=True).order_by("-start_date").first()
    if year is None:
        year = AcademicYear.objects.order_by("-start_date").first()

    for child in Child.objects.all().iterator():
        school_class = classes.get(child.school_class_id)
        if school_class is None:
            continue
        child.school_name = (schools.get(school_class.school_id) or "")[:160]
        child.class_level = _match_level(school_class.name)
        child.save(update_fields=["school_name", "class_level"])
        if year is not None and child.class_level:
            ClassPlacement.objects.get_or_create(
                child_id=child.id,
                academic_year_id=year.id,
                defaults={"class_level": child.class_level},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("children", "0005_class_levels"),
        ("schools", "0002_class_levels"),
    ]

    operations = [
        migrations.RunPython(copy_school_and_class, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="child",
            name="school_class",
        ),
    ]
