"""State-only description of the legacy `cab_g_patient` and `cab_g_patientfile`
tables.

See `cabinets/migrations/0001_initial.py` for why these migrations perform no
database operations: the app split moves no rows, and the tables keep their
original `cab_g_*` names through `Meta.db_table`.

`cin` and `phone` are described here as plain (non-unique) columns because
that is what the database enforces today. The follow-up migration replaces the
two global unique constraints with per-cabinet ones, which the existing 750 rows
satisfy.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cabinets", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Patient",
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
                        ("cin", models.CharField(max_length=25)),
                        ("img", models.ImageField(upload_to="patient/")),
                        ("firstname", models.CharField(max_length=255)),
                        ("lastname", models.CharField(max_length=255)),
                        (
                            "gender",
                            models.CharField(
                                choices=[("Female", "Female"), ("Male", "Male")],
                                max_length=20,
                            ),
                        ),
                        ("age", models.IntegerField(blank=True, null=True)),
                        ("phone", models.CharField(max_length=25)),
                        ("address", models.CharField(max_length=500)),
                        ("child", models.BooleanField(default=False)),
                        (
                            "cabinet",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="patients",
                                to="cabinets.cabinet",
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_patient"},
                ),
                migrations.CreateModel(
                    name="PatientFile",
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
                        ("file", models.FileField(upload_to="patient_documents/")),
                        (
                            "patient",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="files",
                                to="patients.patient",
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_patientfile"},
                ),
            ],
        ),
    ]
