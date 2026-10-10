from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import TimeStampedModel


class Cabinet(TimeStampedModel):
    """A medical practice; the tenant every other resource is scoped to."""

    name = models.CharField(max_length=255)
    number = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Specialite(TimeStampedModel):
    """A medical speciality offered by the practice."""

    name = models.CharField(max_length=250, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Application user. The `role` drives every permission check."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        DOCTOR = "doctor", "Doctor"
        ASSISTANT = "assistant", "Assistant"
        PATIENT = "patient", "Patient"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.ADMIN
    )
    cabinet = models.ForeignKey(
        Cabinet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    def __str__(self):
        return self.get_full_name() or self.username
