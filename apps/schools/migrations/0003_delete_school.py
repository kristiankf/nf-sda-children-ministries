from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0002_class_levels"),
        ("children", "0006_copy_school_class"),
    ]

    operations = [
        migrations.DeleteModel(name="SchoolClass"),
        migrations.DeleteModel(name="School"),
    ]
