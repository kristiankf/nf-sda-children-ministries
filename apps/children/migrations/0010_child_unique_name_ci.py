from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies = [
        ("children", "0009_unique_child_name"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="child",
            constraint=models.UniqueConstraint(
                Lower("first_name"),
                Lower("last_name"),
                name="child_unique_name_ci",
            ),
        ),
    ]
