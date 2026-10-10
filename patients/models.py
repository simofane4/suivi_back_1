from django.db import models

from cabinets.models import Cabinet
from common.constants import GENDER_CHOICES
from common.models import TimeStampedModel


class Patient(TimeStampedModel):
    """A patient of one cabinet.

    `cin` and `phone` were unique across the whole database. Identity documents
    and phone numbers are only meaningful within a country, and two practices
    can legitimately share them, so uniqueness is scoped to the cabinet.
    """

    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name="patients")
    cin = models.CharField(max_length=25)
    img = models.ImageField(upload_to="patient/", default="patient/default.png", blank=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    age = models.IntegerField(blank=True, null=True)
    phone = models.CharField(max_length=25)
    address = models.CharField(max_length=500)
    child = models.BooleanField(
        default=False,
        help_text="Patient is a minor; age is optional and consent rules may apply.",
    )

    class Meta:
        db_table = "cab_g_patient"
        ordering = ("lastname", "firstname")
        constraints = [
            models.UniqueConstraint(
                fields=("cabinet", "cin"),
                name="unique_cin_per_cabinet",
            ),
            models.UniqueConstraint(
                fields=("cabinet", "phone"),
                name="unique_phone_per_cabinet",
            ),
        ]
        indexes = [
            models.Index(fields=("cabinet", "lastname", "firstname"), name="patient_name_idx"),
            models.Index(fields=("cabinet", "phone"), name="patient_phone_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.firstname} {self.lastname}".strip()


class PatientFile(models.Model):
    """A document attached to a patient (scan, photo, report).

    Inheriting the timestamp mixin keeps `created_at` on the existing table, so
    the model stays fully backwards compatible with the stored data.
    """

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="patient_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cab_g_patientfile"
        ordering = ("-uploaded_at",)

    def __str__(self) -> str:
        return f"{self.patient} / {self.file.name}"
