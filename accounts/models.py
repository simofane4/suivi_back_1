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

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.get_full_name() or self.username


class StaffBase(TimeStampedModel):
    """Shared columns for doctors and assistants."""

    class Gender(models.TextChoices):
        MALE = "Male", "Male"
        FEMALE = "Female", "Female"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="%(class)s_profile"
    )
    cabinet = models.ForeignKey(
        Cabinet, on_delete=models.CASCADE, related_name="%(class)ss"
    )
    img = models.ImageField(upload_to="staff/", null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        abstract = True


class Doctor(StaffBase):
    inp = models.CharField(max_length=50, blank=True, default="")
    specialiste = models.ForeignKey(
        Specialite,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Dr {self.user.get_full_name() or self.user.username}"


class Assistant(StaffBase):
    cin = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username
