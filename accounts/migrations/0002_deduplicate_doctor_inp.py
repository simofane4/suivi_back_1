"""Resolve duplicate `Doctor.inp` values before the unique constraint is added.

`Doctor.inp` is a doctor's registration number, which is unique in practice,
but the column carried no constraint. The legacy seed data contains at least
one collision, so adding UNIQUE would fail.

The earliest row keeps the original value; later ones get a `-D<id>` suffix so
the conflict disappears and the affected record stays easy to spot and correct
by hand. Nothing is deleted.
"""

from django.db import connection, migrations


def dedupe_doctor_inp(apps, schema_editor):
    Doctor = apps.get_model("accounts", "Doctor")
    table_name = Doctor._meta.db_table

    if table_name not in connection.introspection.table_names():
        return

    seen = {}
    changed = []

    for pk, inp in Doctor.objects.order_by("pk").values_list("pk", "inp"):
        if inp is None:
            continue
        if inp in seen:
            new_inp = f"{inp}-D{pk}"
            Doctor.objects.filter(pk=pk).update(inp=new_inp)
            changed.append((pk, inp, new_inp))
        else:
            seen[inp] = pk

    if changed:
        print(f"  accounts: resolved {len(changed)} duplicate Doctor.inp value(s):")
        for pk, old, new in changed:
            print(f"    doctor #{pk}: {old!r} -> {new!r} (correct this by hand)")


def noop(apps, schema_editor):
    """Reversing re-adds the constraint, not the duplicate values."""


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(dedupe_doctor_inp, noop),
    ]
