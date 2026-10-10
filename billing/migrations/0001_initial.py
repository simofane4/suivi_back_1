"""State-only description of the legacy `cab_g_invoice` table.

See `cabinets/migrations/0001_initial.py` for why this migration performs no
database operations: the app split moves no rows, and the table keeps its
original name through `Meta.db_table`.

`amount` is described as a DecimalField, which is what the follow-up migration
changes it to on disk; the table is empty so no amount is reinterpreted.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("clinical", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Invoice",
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
                        ("date", models.DateTimeField()),
                        ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                        ("payed", models.BooleanField(default=False)),
                        (
                            "appointment",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="invoices",
                                to="clinical.appointment",
                            ),
                        ),
                        (
                            "recipient",
                            models.ForeignKey(
                                help_text="Staff member the invoice is addressed to.",
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="invoices",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={"db_table": "cab_g_invoice"},
                ),
            ],
        ),
    ]
