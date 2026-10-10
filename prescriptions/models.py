from django.db import models

from core.models import TimeStampedModel


class Ordonnance(TimeStampedModel):
    """A prescription written for an appointment (BE-27/BE-28)."""

    cabinet = models.ForeignKey(
        "accounts.Cabinet", on_delete=models.CASCADE, related_name="ordonnances"
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ordonnances",
    )
    acte_demander = models.ForeignKey(
        "catalog.ActeDemander",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordonnances",
    )
    acte_fait = models.ForeignKey(
        "catalog.ActeFait",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordonnances",
    )
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ordonnance #{self.pk}"


class OrdonnanceLine(TimeStampedModel):
    """One medicine line of an ordonnance."""

    ordonnance = models.ForeignKey(
        Ordonnance, on_delete=models.CASCADE, related_name="lines"
    )
    medicament = models.ForeignKey(
        "catalog.Medicament", on_delete=models.CASCADE, related_name="ordonnance_lines"
    )
    dosage = models.CharField(max_length=100, blank=True, default="")
    duration = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.medicament} ({self.dosage})"