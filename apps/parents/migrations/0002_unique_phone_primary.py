from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("parents", "0001_initial"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="parent",
            name="parents_par_phone_p_61f077_idx",
        ),
        migrations.AddConstraint(
            model_name="parent",
            constraint=models.UniqueConstraint(
                fields=("phone_primary",),
                name="parent_unique_phone_primary",
            ),
        ),
    ]
