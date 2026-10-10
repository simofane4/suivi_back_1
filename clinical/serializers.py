from django.db import transaction
from rest_framework import serializers

from cabinets.models import Cabinet
from patients.models import Patient

from .models import (
    ActeDemander,
    ActeFait,
    Appointment,
    Medicament,
    Ordonnance,
    OrdonnanceMedicament,
)
from .services import validate_appointment_slot


class ActeDemanderSerializer(serializers.ModelSerializer):
    # Optional in the payload: staff have their cabinet forced from the token by
    # CabinetScopedMixin, only an admin has to name one.
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all(), required=False)

    class Meta:
        model = ActeDemander
        fields = ("id", "cabinet", "title", "description", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class ActeFaitSerializer(serializers.ModelSerializer):
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all(), required=False)

    class Meta:
        model = ActeFait
        fields = ("id", "cabinet", "title", "description", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class MedicamentSerializer(serializers.ModelSerializer):
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all(), required=False)

    class Meta:
        model = Medicament
        fields = ("id", "cabinet", "name", "description", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all(), required=False)

    class Meta:
        model = Appointment
        fields = (
            "id",
            "patient",
            "patient_name",
            "cabinet",
            "date",
            "start",
            "end",
            "description",
            "payed",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_patient_name(self, obj) -> str:
        return f"{obj.patient.firstname} {obj.patient.lastname}".strip()

    def validate(self, attrs):
        patient = attrs.get("patient") or getattr(self.instance, "patient", None)
        if patient is None:
            raise serializers.ValidationError({"patient": "Ce champ est obligatoire."})

        cabinet = attrs.get("cabinet") or getattr(self.instance, "cabinet", None)
        if cabinet is None:
            cabinet = patient.cabinet
        if patient.cabinet_id != cabinet.id:
            raise serializers.ValidationError(
                {"patient": "Le patient n'appartient pas a ce cabinet."}
            )

        date = attrs.get("date") or getattr(self.instance, "date", None)
        start = attrs.get("start") or getattr(self.instance, "start", None)
        end = attrs.get("end") or getattr(self.instance, "end", None)

        if date and start and end:
            same_day = Appointment.objects.filter(cabinet=cabinet, date=date)
            validate_appointment_slot(
                date=date,
                start=start,
                end=end,
                queryset=same_day,
                exclude_pk=getattr(self.instance, "pk", None),
            )
        return attrs


class OrdonnanceMedicamentSerializer(serializers.ModelSerializer):
    medicament_name = serializers.CharField(source="medicament.name", read_only=True)

    class Meta:
        model = OrdonnanceMedicament
        fields = ("id", "medicament", "medicament_name", "dosage", "duration")


class OrdonnanceSerializer(serializers.ModelSerializer):
    medicaments_list = OrdonnanceMedicamentSerializer(source="ordonnancemedicament_set", many=True, read_only=True)
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all(), required=False)

    class Meta:
        model = Ordonnance
        fields = (
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
        )
        # `cabinet` stays writable so an admin, who has no cabinet of its own,
        # can create an ordonnance. Staff cannot abuse it: the base viewset
        # forces their own cabinet on both create and update.
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        # For updates, if appointment is not provided, use the instance's appointment
        appointment = attrs.get("appointment") or getattr(self.instance, "appointment", None)
        if appointment is None:
            raise serializers.ValidationError({"appointment": "Ce champ est obligatoire."})

        cabinet = attrs.get("cabinet") or getattr(self.instance, "cabinet", None)
        if cabinet is None:
            cabinet = appointment.cabinet
        if appointment.cabinet_id != cabinet.id:
            raise serializers.ValidationError(
                {"appointment": "Le rendez-vous n'appartient pas a ce cabinet."}
            )

        # Reject references to another cabinet's catalogue entries.
        for field in ("acte_demander", "acte_fait"):
            value = attrs.get(field)
            if value is not None and value.cabinet_id != cabinet.id:
                raise serializers.ValidationError(
                    {field: "Cette entrée appartient a un autre cabinet."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        medicaments = validated_data.pop("medicaments", [])
        ordonnance = Ordonnance.objects.create(**validated_data)
        ordonnance.medicaments.set(medicaments)
        return ordonnance

    @transaction.atomic
    def update(self, instance, validated_data):
        medicaments = validated_data.pop("medicaments", None)
        instance = super().update(instance, validated_data)
        if medicaments is not None:
            instance.medicaments.set(medicaments)
        return instance
