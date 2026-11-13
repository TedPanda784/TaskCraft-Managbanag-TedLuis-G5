import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="phone_number",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddConstraint(
            model_name="customuser",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("email"),
                condition=models.Q(("email", ""), _negated=True),
                name="unique_nonempty_user_email_ci",
            ),
        ),
    ]
