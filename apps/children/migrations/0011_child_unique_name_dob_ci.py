from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies = [
        ("children", "0010_child_unique_name_ci"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="child",
            name="child_unique_name_ci",
        ),
        migrations.AddConstraint(
            model_name="child",
            constraint=models.UniqueConstraint(
                Lower("first_name"),
                Lower("last_name"),
                "date_of_birth",
                name="child_unique_name_dob_ci",
            ),
        ),
    ]
