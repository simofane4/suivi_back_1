from django.db import models

from cabinets.models import Cabinet
from common.models import TimeStampedModel
from patients.models import Patient


class ActeDemander(TimeStampedModel):
    """A procedure the practice offers. Cabinet-scoped catalogue entry."""

    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name="actes_demandes")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "cab_g_actedemander"
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title


class ActeFait(TimeStampedModel):
    """A procedure that was performed. Cabinet-scoped catalogue entry."""

    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name="actes_faits")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "cab_g_actefait"
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title


class Medicament(TimeStampedModel):
    """A medication stocked by the practice."""

    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name="medicaments")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "cab_g_medicament"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Appointment(TimeStampedModel):
    """A scheduled visit.

    Carries its own `cabinet` so that availability can be checked without
    joining through `Patient`, and so an appointment cannot end up belonging to
    a different cabinet than its patient.
    """

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    cabinet = models.ForeignKey(
        Cabinet,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    date = models.DateField()
    start = models.TimeField(db_column="fm")
    end = models.TimeField(db_column="To")
    description = models.TextField(blank=True)
    payed = models.BooleanField(default=False)

    class Meta:
        db_table = "cab_g_appointment"
        ordering = ("date", "start")
        indexes = [
            # Drives the availability query, which always filters on cabinet+date.
            models.Index(fields=("cabinet", "date"), name="appointment_cab_date_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end__gt=models.F("start")),
                name="appointment_end_after_start",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.patient} {self.date} {self.start:%H:%M}-{self.end:%H:%M}"

    @property
    def duration_minutes(self) -> int:
        start = self.start.hour * 60 + self.start.minute
        end = self.end.hour * 60 + self.end.minute
        return end - start


class Ordonnance(TimeStampedModel):
    """A prescription issued during an appointment.

    The original model pointed `appointment` at `Patient`, so a prescription
    could not reference the visit it was written for. It now targets the real
    `Appointment`. The table is empty, so retargeting the column is free.
    """

    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name="ordonnances")
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="ordonnances",
    )
    acte_demander = models.ForeignKey(
        ActeDemander,
        on_delete=models.SET_NULL,
        related_name="ordonnances",
        blank=True,
        null=True,
    )
    acte_fait = models.ForeignKey(
        ActeFait,
        on_delete=models.SET_NULL,
        related_name="ordonnances",
        blank=True,
        null=True,
    )
    medicaments = models.ManyToManyField(
        Medicament,
        through="OrdonnanceMedicament",
        related_name="ordonnances",
    )
    description = models.TextField()

    class Meta:
        db_table = "cab_g_ordonnance"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Ordonnance #{self.pk} - {self.appointment_id}"


class OrdonnanceMedicament(models.Model):
    """Explicit through model for the prescription lines.

    Named explicitly for two reasons: the auto-generated table name would not
    match the existing `cab_g_ordonnance_medicament` once `db_table` is set on
    both sides, and it leaves room for dose and duration fields later.
    """

    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE)
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=255, blank=True, default="")
    duration = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "cab_g_ordonnance_medicament"
        constraints = [
            models.UniqueConstraint(
                fields=("ordonnance", "medicament"),
                name="unique_medicament_per_ordonnance",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ordonnance_id} / {self.medicament_id}"
