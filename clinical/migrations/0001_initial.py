"""State-only description of the legacy `cab_g_*` clinical tables.

See `cabinets/migrations/0001_initial.py` for why these migrations perform no
database operations: the app split moves no rows, and the tables keep their
original `cab_g_*` names through `Meta.db_table`.

Two details worth knowing:

* `Appointment.start` / `.end` describe the legacy `fm` / `"To"` columns via
  `db_column`, so the three stored appointments keep their times without any
  column rename.
* `Ordonnance.appointment` is described here as pointing at `Appointment`
  rather than `Patient`, which was a bug: a prescription could not reference the
  visit it was written for. The column now holds appointment ids and the table
  is empty, so nothing is reinterpreted.
* `OrdonnanceMedicament` is declared as an explicit through model so its table
  keeps the name `cab_g_ordonnance_medicament`; Django's automatic name would
  not match once `db_table` is set on both sides. Only the two columns that
  already exist are listed -- `dosage` and `duration` are genuinely new and
  are added by the following migration.

Fields whose column does **not** yet exist in the database are deliberately
absent below. Claiming a column in state that the table does not have makes
Django's SQLite table rebuild write the field name into the new column instead
of a value, so those are left for a real `AddField`.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cabinets", "0001_initial"),
        ("patients", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="ActeDemander",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("title", models.CharField(max_length=255)),
                        ("description", models.TextField(blank=True, null=True)),
                        (
                            "cabinet",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="actes_demandes",
                                to="cabinets.cabinet",
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_actedemander"},
                ),
                migrations.CreateModel(
                    name="ActeFait",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("title", models.CharField(max_length=255)),
                        ("description", models.TextField(blank=True, null=True)),
                        (
                            "cabinet",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="actes_faits",
                                to="cabinets.cabinet",
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_actefait"},
                ),
                migrations.CreateModel(
                    name="Medicament",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("name", models.CharField(max_length=255)),
                        ("description", models.TextField(blank=True, null=True)),
                        (
                            "cabinet",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="medicaments",
                                to="cabinets.cabinet",
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_medicament"},
                ),
                migrations.CreateModel(
                    name="Appointment",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("date", models.DateField()),
                        ("start", models.TimeField(db_column="fm")),
                        ("end", models.TimeField(db_column="To")),
                        ("description", models.TextField(blank=True)),
                        ("payed", models.BooleanField(default=False)),
                        (
                            "patient",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="appointments",
                                to="patients.patient",
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_appointment"},
                ),
                migrations.CreateModel(
                    name="Ordonnance",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("description", models.TextField()),
                        (
                            "acte_demander",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="ordonnances",
                                to="clinical.actedemander",
                            ),
                        ),
                        (
                            "acte_fait",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="ordonnances",
                                to="clinical.actefait",
                            ),
                        ),
                        (
                            "appointment",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="ordonnances",
                                to="clinical.appointment",
                            ),
                        ),
                        (
                            "cabinet",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="ordonnances",
                                to="cabinets.cabinet",
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_ordonnance"},
                ),
                migrations.CreateModel(
                    name="OrdonnanceMedicament",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "medicament",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="clinical.medicament",
                            ),
                        ),
                        (
                            "ordonnance",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="clinical.ordonnance",
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_ordonnance_medicament"},
                ),
                migrations.AddField(
                    model_name="ordonnance",
                    name="medicaments",
                    field=models.ManyToManyField(
                        related_name="ordonnances",
                        through="clinical.OrdonnanceMedicament",
                        to="clinical.medicament",
                    ),
                ),
            ],
        ),
    ]
