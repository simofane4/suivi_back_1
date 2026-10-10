from django.contrib.auth import get_user_model
from django.db import models

from core.models import TimeStampedModel


class Patient(TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = "Male", "Male"
        FEMALE = "Female", "Female"

    cabinet = models.ForeignKey(
        "accounts.Cabinet", on_delete=models.CASCADE, related_name="patients"
    )
    cin = models.CharField(max_length=50)
    img = models.ImageField(upload_to="patients/", null=True, blank=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=500, blank=True, null=True)
    child = models.BooleanField(default=False)
    assurance = models.CharField(max_length=150, blank=True, default="")
    numero_adherent = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        ordering = ["lastname", "firstname"]
        constraints = [
            models.UniqueConstraint(
                fields=["cabinet", "cin"], name="uniq_patient_cin_per_cabinet"
            ),
        ]

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class PatientFile(models.Model):
    """Document attached to a patient; inherits its cabinet from the patient."""

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="files"
    )
    file = models.FileField(upload_to="patient_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_files",
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.patient} - {self.file.name}"


class Antecedent(TimeStampedModel):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="antecedents"
    )
    label = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.label


class Allergie(TimeStampedModel):
    class Severity(models.TextChoices):
        LEGERE = "Légère", "Légère"
        MODEREE = "Modérée", "Modérée"
        SEVERE = "Sévère", "Sévère"

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="allergies"
    )
    name = models.CharField(max_length=255)
    severity = models.CharField(
        max_length=20, choices=Severity.choices, default=Severity.LEGERE
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Observation(TimeStampedModel):
    """A consultation note with an ICD-10 diagnostic code."""

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="observations"
    )
    diagnostic = models.CharField(max_length=10)
    diagnostic_label = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_observations",
    )

    class Meta:
        ordering = ["-created_at", "-version"]

    def __str__(self):
        return self.diagnostic