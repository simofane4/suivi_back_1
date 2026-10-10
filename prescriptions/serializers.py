from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.models import Cabinet
from catalog.models import ActeDemander, ActeFait, Medicament
from core.permissions import ADMIN

from .models import Ordonnance, OrdonnanceLine


class OrdonnanceMedicamentInputSerializer(serializers.Serializer):
    medicament = serializers.PrimaryKeyRelatedField(
        queryset=Medicament.objects.all()
    )
    dosage = serializers.CharField(required=False, allow_blank=True, default="")
    duration = serializers.CharField(required=False, allow_blank=True, default="")


class OrdonnanceMedicamentReadSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    medicament = serializers.IntegerField()
    medicament_name = serializers.CharField()
    dosage = serializers.CharField()
    duration = serializers.CharField()


class OrdonnanceSerializer(serializers.ModelSerializer):
    cabinet = serializers.PrimaryKeyRelatedField(
        queryset=Cabinet.objects.all(), required=False
    )
    acte_demander = serializers.PrimaryKeyRelatedField(
        queryset=ActeDemander.objects.all(), required=False, allow_null=True
    )
    acte_fait = serializers.PrimaryKeyRelatedField(
        queryset=ActeFait.objects.all(), required=False, allow_null=True
    )
    medicaments = OrdonnanceMedicamentInputSerializer(
        many=True, write_only=True, required=False
    )
    medicaments_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ordonnance
        fields = [
            "id",
            "cabinet",
            "appointment",
            "acte_demander",
            "acte_fait",
            "description",
            "medicaments",
            "medicaments_list",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    @extend_schema_field(OrdonnanceMedicamentReadSerializer(many=True))
    def get_medicaments_list(self, obj) -> list[dict]:
        lines = obj.lines.select_related("medicament").all()
        return [
            {
                "id": line.id,
                "medicament": line.medicament_id,
                "medicament_name": line.medicament.name_fr or line.medicament.name,
                "dosage": line.dosage,
                "duration": line.duration,
            }
            for line in lines
        ]

    def _is_admin(self):
        user = self.context["request"].user
        return bool(user.is_superuser or getattr(user, "role", None) == ADMIN)

    def validate(self, attrs):
        appointment = attrs.get("appointment", getattr(self.instance, "appointment", None))
        if appointment is None:
            return attrs
        user = self.context["request"].user
        cabinet = attrs.get("cabinet") or getattr(
            self.instance, "cabinet", None
        ) or getattr(user, "cabinet", None)
        if (
            not self._is_admin()
            and appointment.cabinet_id != (cabinet.pk if cabinet else user.cabinet_id)
        ):
            raise serializers.ValidationError(
                {"appointment": "Le rendez-vous n'appartient pas à votre cabinet."}
            )
        return attrs

    def _rebuild_lines(self, ordonnance, items):
        ordonnance.lines.all().delete()
        for item in items:
            OrdonnanceLine.objects.create(ordonnance=ordonnance, **item)

    def create(self, validated_data):
        items = validated_data.pop("medicaments", [])
        user = self.context["request"].user
        if not self._is_admin():
            validated_data["cabinet"] = user.cabinet
        appointment = validated_data.get("appointment")
        if "cabinet" not in validated_data and appointment is not None:
            validated_data["cabinet"] = appointment.cabinet
        ordonnance = Ordonnance.objects.create(**validated_data)
        self._rebuild_lines(ordonnance, items)
        return ordonnance

    def update(self, instance, validated_data):
        items = validated_data.pop("medicaments", None)
        if not self._is_admin():
            validated_data.pop("cabinet", None)
        ordonnance = super().update(instance, validated_data)
        if items is not None:
            self._rebuild_lines(ordonnance, items)
        return ordonnance