from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.db.models.functions import Lower


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT
    )

    course = models.CharField(
        max_length=100,
        blank=True
    )

    phone_number = models.CharField(max_length=30, blank=True)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                condition=~Q(email=""),
                name="unique_nonempty_user_email_ci",
            ),
        ]

    def __str__(self):
        return self.username