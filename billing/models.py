from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel

CENT = Decimal("0.01")

ASSURANCE_RATIOS = {
    "CNOPS": Decimal("80"),
    "CNAMGS": Decimal("80"),
    "CNSS": Decimal("70"),
    "FAR": Decimal("80"),
}


def ratio_for_assurance(assurance: str) -> Decimal:
    label = (assurance or "").strip().upper()
    for key, ratio in ASSURANCE_RATIOS.items():
        if key in label:
            return ratio
    return Decimal("0")


class Invoice(TimeStampedModel):
    """A bill for an appointment; split between patient and insurance.

    The API.md contract only exposes `payed`, but the full plan also tracks
    per-item lines, payments and the amounts still owed by each party.
    """

    class Status(models.TextChoices):
        UNPAID = "unpaid", "Non payée"
        PARTIALLY_PAID = "partially_paid", "Partiellement payée"
        PAID = "paid", "Payée"

    cabinet = models.ForeignKey(
        "accounts.Cabinet", on_delete=models.CASCADE, related_name="invoices"
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    date = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    organisme_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_invoices",
    )
    payed = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UNPAID
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Facture #{self.pk} — {self.status}"

    @property
    def patient(self):
        return self.appointment.patient

    @property
    def organisme_share(self):
        return (self.amount * self.organisme_ratio / 100).quantize(
            CENT, ROUND_HALF_UP
        )

    @property
    def patient_share(self):
        return (self.amount - self.organisme_share).quantize(CENT, ROUND_HALF_UP)

    def _payments(self):
        # Never use `self.payments.all()` here: viewsets prefetch the reverse
        # relation and the prefetched cache goes stale as soon as a payment is
        # created after the queryset was built.
        return Payment.objects.filter(invoice=self)

    def _paid_split(self):
        patient_paid = Decimal("0")
        organisme_paid = Decimal("0")
        for payment in self._payments():
            if payment.kind == Payment.Kind.ORGANISME:
                organisme_paid += payment.amount
            else:
                patient_paid += payment.amount
        return patient_paid, organisme_paid

    @property
    def patient_paid(self):
        return self._paid_split()[0]

    @property
    def organisme_paid(self):
        return self._paid_split()[1]

    @property
    def total_paid(self):
        return self.patient_paid + self.organisme_paid

    @property
    def patient_rest(self):
        return max(self.patient_share - self.patient_paid, CENT * 0)

    @property
    def organisme_rest(self):
        return max(self.organisme_share - self.organisme_paid, CENT * 0)

    def refresh_status(self):
        """Recompute `status`/`payed` from the recorded payments."""
        amount = Decimal(str(self.amount))
        if self.total_paid >= amount:
            self.status = self.Status.PAID
        elif self.total_paid > 0:
            self.status = self.Status.PARTIALLY_PAID
        else:
            self.status = self.Status.UNPAID
        self.payed = self.status == self.Status.PAID
        self.save(update_fields=["status", "payed", "updated_at"])


class InvoiceItem(TimeStampedModel):
    """A single billed line inside an invoice."""

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="items"
    )
    label = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.label} — {self.amount}"


class Payment(TimeStampedModel):
    """A payment received: from the patient or from the insurance organism."""

    class Kind(models.TextChoices):
        PATIENT = "patient", "Patient"
        ORGANISME = "organisme", "Organisme"

    class Method(models.TextChoices):
        CASH = "cash", "Espèces"
        CARD = "card", "Carte"
        CHEQUE = "cheque", "Chèque"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    kind = models.CharField(
        max_length=20, choices=Kind.choices, default=Kind.PATIENT
    )
    method = models.CharField(
        max_length=20, choices=Method.choices, default=Method.CASH
    )
    note = models.CharField(max_length=255, blank=True, default="")
    paid_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_payments",
    )

    class Meta:
        ordering = ["-paid_at", "-id"]

    def __str__(self):
        return f"{self.amount} DH ({self.kind})"