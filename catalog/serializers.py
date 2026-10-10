from rest_framework import serializers

from accounts.models import Cabinet
from core.permissions import ADMIN

from .models import ActeDemander, ActeFait, Medicament


class CabinetForcedOnCreateMixin:
    """Staff cannot choose a cabinet: it is taken from their token."""

    def _is_admin(self):
        user = self.context["request"].user
        return bool(user.is_superuser or getattr(user, "role", None) == ADMIN)

    def create(self, validated_data):
        if self._is_admin():
            if validated_data.get("cabinet") is None:
                raise serializers.ValidationError(
                    {"cabinet": "Ce champ est obligatoire pour un administrateur."}
                )
        else:
            validated_data["cabinet"] = self.context["request"].user.cabinet
        return super().create(validated_data)


class CabinetOwnerField(serializers.PrimaryKeyRelatedField):
    """Cabinet the admin picks; staff resolve it from their token instead."""

    def __init__(self, **kwargs):
        kwargs.setdefault("queryset", Cabinet.objects.all())
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)


class MedicamentSerializer(CabinetForcedOnCreateMixin, serializers.ModelSerializer):
    cabinet = CabinetOwnerField()

    class Meta:
        model = Medicament
        fields = [
            "id",
            "cabinet",
            "name",
            "name_fr",
            "name_ar",
            "form",
            "dosage",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ActeDemanderSerializer(CabinetForcedOnCreateMixin, serializers.ModelSerializer):
    cabinet = CabinetOwnerField()

    class Meta:
        model = ActeDemander
        fields = [
            "id",
            "cabinet",
            "title",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ActeFaitSerializer(CabinetForcedOnCreateMixin, serializers.ModelSerializer):
    cabinet = CabinetOwnerField()

    class Meta:
        model = ActeFait
        fields = [
            "id",
            "cabinet",
            "title",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]