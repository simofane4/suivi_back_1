"""State-only description of the legacy `cab_g_cabinet` and `cab_g_specialite`
tables.

The project started as a single `cab_g` app and has been split into five
per-domain apps. Splitting an app moves no rows, so the tables created by
`cab_g/migrations/0001_initial.py` are still present under their original
`cab_g_*` names, kept via `Meta.db_table`.

This migration therefore performs **no** database operations. It only records
model state, so that a follow-up migration can compute the genuine schema delta
-- the timestamps and the new uniqueness constraint -- and apply it.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Cabinet",
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
                        ("number", models.CharField(max_length=255, unique=True)),
                        ("address", models.CharField(blank=True, max_length=500, null=True)),
                    ],
                    options={"db_table": "cab_g_cabinet"},
                ),
                migrations.CreateModel(
                    name="Specialite",
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
                        ("name", models.CharField(max_length=250)),
                    ],
                    options={"db_table": "cab_g_specialite"},
                ),
            ],
        ),
    ]
