from django.db import models
from django.utils import timezone

from accounts.models import Cabinet, Doctor
from core.models import TimeStampedModel
from patients.models import Patient


class Appointment(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    cabinet = models.ForeignKey(
        Cabinet, on_delete=models.CASCADE, related_name="appointments"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="appointments"
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="appointments",
    )
    start = models.DateTimeField()
    end = models.DateTimeField()
    date = models.DateField(editable=False)
    reason = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    payed = models.BooleanField(default=False)

    class Meta:
        ordering = ["start"]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["cabinet", "date"]),
        ]

    def save(self, *args, **kwargs):
        if self.start:
            local = self.start
            if self.start.tzinfo is not None:
                local = timezone.localtime(self.start)
            self.date = local.date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient} @ {self.date} {self.start:%H:%M}"