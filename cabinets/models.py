from django.db import models

from common.models import TimeStampedModel


class Cabinet(TimeStampedModel):
    """A medical practice. Every other record in the system belongs to one."""

    name = models.CharField(max_length=255)
    number = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "cab_g_cabinet"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Specialite(models.Model):
    """A medical speciality. Global reference data, not cabinet-scoped."""

    name = models.CharField(max_length=250, unique=True)

    class Meta:
        db_table = "cab_g_specialite"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name
