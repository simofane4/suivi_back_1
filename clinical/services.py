"""Appointment availability.

The original check lived inline in a view and returned HTTP 201 for conflicts,
parsed times with `strptime` on raw strings, and never handled a requested
interval that enclosed an existing one. This module is the single
implementation, called from the serializer.
"""

from dataclasses import dataclass

from django.utils import timezone

from rest_framework.exceptions import ValidationError


@dataclass(frozen=True)
class Slot:
    start: object  # datetime.time
    end: object  # datetime.time


def _overlaps(a: Slot, b: Slot) -> bool:
    """Half-open interval overlap: touching endpoints do not conflict."""
    return a.start < b.end and b.start < a.end


def find_conflicts(appointments, slot: Slot) -> list:
    return [appointment for appointment in appointments if _overlaps(slot, Slot(appointment.start, appointment.end))]


def validate_appointment_slot(
    *,
    date,
    start,
    end,
    queryset,
    exclude_pk=None,
    allow_past=False,
) -> None:
    """Raise `ValidationError` if the requested slot cannot be booked.

    `queryset` must already be limited to the cabinet and the given date.
    """
    if end <= start:
        raise ValidationError({"end": "L'heure de fin doit etre posterieure a l'heure de debut."})

    today = timezone.localdate()
    if not allow_past and date < today:
        raise ValidationError({"date": f"La date {date} est deja passee."})

    conflicts = find_conflicts(queryset, Slot(start=start, end=end))
    if exclude_pk is not None:
        conflicts = [conflict for conflict in conflicts if conflict.pk != exclude_pk]

    if conflicts:
        detail = ", ".join(
            f"{conflict.start:%H:%M}-{conflict.end:%H:%M}" for conflict in conflicts
        )
        raise ValidationError(
            {
                "start": (
                    f"Ce creneau chevauche un rendez-vous existant ({detail}). "
                    "Choisissez un autre horaire."
                )
            }
        )
