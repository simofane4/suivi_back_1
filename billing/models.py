from django.contrib.auth.models import User
from django.db import models

from clinical.models import Appointment
from common.models import TimeStampedModel


class Invoice(TimeStampedModel):
    """A charge attached to an appointment.

    Scoping is via `appointment__cabinet`. The old code filtered
    `recipient` -- a FK to `auth_user` -- against a *cabinet* id, so the
    endpoint never returned the caller's invoices.

    `amount` moved from IntegerField to DecimalField: money stored as an integer
    invites ambiguity over units and truncation. The table is empty, so
    changing the column costs nothing.
    """

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    date = models.DateTimeField()
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="invoices",
        help_text="Staff member the invoice is addressed to.",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payed = models.BooleanField(default=False)

    class Meta:
        db_table = "cab_g_invoice"
        ordering = ("-date",)
        indexes = [
            models.Index(fields=("appointment", "date"), name="invoice_appt_date_idx"),
        ]

    def __str__(self) -> str:
        # The original referenced `self.status`, which is not a field, so
        # printing any invoice raised AttributeError.
        state = "payee" if self.payed else "non payee"
        return f"Facture #{self.pk} - {self.amount} ({state})"
