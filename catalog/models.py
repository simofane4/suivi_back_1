from django.db import models

from core.models import TimeStampedModel


class CabinetOwnedCatalog(TimeStampedModel):
    """Reference row owned by a cabinet (medicine or medical act)."""

    cabinet = models.ForeignKey(
        "accounts.Cabinet",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ["id"]


class Medicament(CabinetOwnedCatalog):
    name = models.CharField(max_length=255)
    name_fr = models.CharField(max_length=255, blank=True, default="")
    name_ar = models.CharField(max_length=255, blank=True, default="")
    form = models.CharField(max_length=100, blank=True, default="")
    dosage = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name_fr or self.name


class ActeDemander(CabinetOwnedCatalog):
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class ActeFait(CabinetOwnedCatalog):
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
