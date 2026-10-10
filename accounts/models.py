from django.contrib.auth.models import User
from django.db import models

from cabinets.models import Cabinet, Specialite
from common.constants import GENDER_CHOICES
from common.models import TimeStampedModel


class Doctor(TimeStampedModel):
    """A doctor, linked 1:1 to a `User` account.

    `related_name="doctor"` is what lets `request.user.doctor.cabinet` resolve
    the caller's clinic; `common.tenancy` relies on it.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor")
    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name="doctors")
    img = models.ImageField(upload_to="doctor/", default="doctor/default.png", blank=True)
    # Numero d'inscription a l'ordre des medecins.
    inp = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=30, unique=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    # Was RESTRICT, renamed to PROTECT in Django 3.1.
    specialiste = models.ForeignKey(Specialite, on_delete=models.PROTECT, related_name="doctors")

    class Meta:
        db_table = "cab_g_doctor"
        ordering = ("user__last_name", "user__first_name")

    def __str__(self) -> str:
        return f"Dr {self.user.first_name} {self.user.last_name}".strip()


class Assistant(TimeStampedModel):
    """A practice assistant, linked 1:1 to a `User` account."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="assistant")
    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name="assistants")
    img = models.ImageField(upload_to="assistant/", default="assistant/default.png", blank=True)
    cin = models.CharField(max_length=25, unique=True, null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=30, unique=True)
    address = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "cab_g_assistant"
        ordering = ("user__last_name", "user__first_name")

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}".strip()
