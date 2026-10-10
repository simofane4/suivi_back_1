"""State-only description of the legacy `cab_g_doctor` and `cab_g_assistant`
tables.

See `cabinets/migrations/0001_initial.py` for why these migrations perform no
database operations: the app split moves no rows, and the tables keep their
original `cab_g_*` names through `Meta.db_table`.

Field names here already match the current models -- `related_name="doctor"` /
`"assistant"` is what makes `request.user.doctor.cabinet` resolve -- so the only
real work left for the next migration is adding timestamps and the unique
constraint on `Doctor.inp`.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cabinets", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Doctor",
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
                        ("img", models.ImageField(upload_to="doctor/")),
                        ("inp", models.CharField(max_length=255)),
                        (
                            "gender",
                            models.CharField(
                                choices=[("Female", "Female"), ("Male", "Male")],
                                max_length=20,
                            ),
                        ),
                        ("phone", models.CharField(max_length=30, unique=True)),
                        ("address", models.CharField(blank=True, max_length=500, null=True)),
                        (
                            "cabinet",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="doctors",
                                to="cabinets.cabinet",
                            ),
                        ),
                        (
                            "specialiste",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.PROTECT,
                                related_name="doctors",
                                to="cabinets.specialite",
                            ),
                        ),
                        (
                            "user",
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="doctor",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_doctor"},
                ),
                migrations.CreateModel(
                    name="Assistant",
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
                        ("img", models.ImageField(upload_to="assistant/")),
                        ("cin", models.CharField(blank=True, max_length=25, null=True, unique=True)),
                        (
                            "gender",
                            models.CharField(
                                choices=[("Female", "Female"), ("Male", "Male")],
                                max_length=20,
                            ),
                        ),
                        ("phone", models.CharField(max_length=30, unique=True)),
                        ("address", models.CharField(blank=True, max_length=500, null=True)),
                        (
                            "cabinet",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="assistants",
                                to="cabinets.cabinet",
                            ),
                        ),
                        (
                            "user",
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="assistant",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_assistant"},
                ),
            ],
        ),
    ]
