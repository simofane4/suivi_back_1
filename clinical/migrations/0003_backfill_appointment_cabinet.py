"""Backfill `Appointment.cabinet` from the patient's cabinet, then make it
mandatory.

`Appointment` gained its own `cabinet` link so availability can be checked
without joining through `Patient`, and so an appointment cannot end up in a
different clinic than its patient. The column was added by the previous
migration; this fills it in for the rows that predate it and then tightens it
to NOT NULL.

An appointment whose patient row is missing is reported and left null, so the
tightening fails loudly instead of silently attaching it to the wrong clinic.
"""

import django.db.models.deletion
from django.db import migrations, models


def backfill_appointment_cabinet(apps, schema_editor):
    Appointment = apps.get_model("clinical", "Appointment")

    orphans = []
    rows = 0

    for appointment in (
        Appointment.objects.select_related("patient").order_by("pk").iterator()
    ):
        if appointment.cabinet_id is not None:
            continue
        patient = appointment.patient
        if patient is None or patient.cabinet_id is None:
            orphans.append(appointment.pk)
            continue
        Appointment.objects.filter(pk=appointment.pk).update(cabinet_id=patient.cabinet_id)
        rows += 1

    if rows:
        print(f"  clinical: backfilled cabinet on {rows} appointment(s)")
    if orphans:
        print(
            "  clinical: WARNING appointments with no cabinet to inherit from: "
            f"{orphans}"
        )


def noop(apps, schema_editor):
    """Reversing restores nullability but leaves the backfilled values in place."""


class Migration(migrations.Migration):
    dependencies = [
        ("clinical", "0002_timestamps_indexes_and_constraints"),
        ("patients", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_appointment_cabinet, noop),
        migrations.AlterField(
            model_name="appointment",
            name="cabinet",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="appointments",
                to="cabinets.cabinet",
            ),
        ),
    ]
