from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.models import Cabinet
from core.permissions import ADMIN

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    cabinet = serializers.PrimaryKeyRelatedField(
        queryset=Cabinet.objects.all(), required=False
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "cabinet",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "date",
            "start",
            "end",
            "reason",
            "status",
            "payed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "date", "created_at", "updated_at"]

    def get_patient_name(self, obj) -> str:
        return str(obj.patient)

    @extend_schema_field(str)
    def get_doctor_name(self, obj):
        return str(obj.doctor) if obj.doctor_id else None

    def validate(self, attrs):
        user = self.context["request"].user
        instance = self.instance
        is_admin = user.is_superuser or getattr(user, "role", None) == ADMIN

        cabinet = attrs.get("cabinet")
        if not is_admin:
            cabinet = user.cabinet
        elif cabinet is None and instance is not None:
            cabinet = instance.cabinet

        start = attrs.get("start") or (instance.start if instance else None)
        end = attrs.get("end") or (instance.end if instance else None)

        if start is None or end is None:
            return attrs

        if end <= start:
            raise serializers.ValidationError(
                "L'heure de fin doit être après l'heure de début."
            )

        if start.tzinfo is None:
            start = timezone.make_aware(start)
        if start < timezone.now():
            raise serializers.ValidationError(
                {"start": "Le rendez-vous ne peut pas être prévu dans le passé."}
            )

        if cabinet is not None and self._overlap(cabinet, start, end, instance):
            raise serializers.ValidationError(
                "Un rendez-vous chevauche déjà ce créneau."
            )
        return attrs

    def _overlap(self, cabinet, start, end, instance=None):
        queryset = Appointment.objects.filter(
            cabinet=cabinet, start__lt=end, end__gt=start
        ).exclude(status=Appointment.Status.CANCELLED)
        if instance is not None:
            queryset = queryset.exclude(pk=instance.pk)
        return queryset.exists()

    def create(self, validated_data):
        user = self.context["request"].user
        if not (user.is_superuser or getattr(user, "role", None) == ADMIN):
            validated_data["cabinet"] = user.cabinet
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not (user.is_superuser or getattr(user, "role", None) == ADMIN):
            validated_data.pop("cabinet", None)
        return super().update(instance, validated_data)