from rest_framework import serializers
from django.utils import timezone

from .models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    recipient_username = serializers.CharField(source="recipient.username", read_only=True)
    date = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "appointment",
            "patient_name",
            "date",
            "recipient",
            "recipient_username",
            "amount",
            "payed",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
        extra_kwargs = {"recipient": {"required": False}}

    def get_patient_name(self, obj) -> str:
        patient = obj.appointment.patient
        return f"{patient.firstname} {patient.lastname}".strip()

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Le montant ne peut pas etre negatif.")
        return value

    def validate(self, attrs):
        appointment = attrs.get("appointment") or getattr(self.instance, "appointment", None)
        if appointment is None:
            raise serializers.ValidationError({"appointment": "Ce champ est obligatoire."})

        recipient = attrs.get("recipient") or getattr(self.instance, "recipient", None)
        if recipient is None:
            # Default to the caller so a client does not have to send its own id.
            recipient = self.context["request"].user
            attrs["recipient"] = recipient

        # Default the date to now if not provided
        if "date" not in attrs or attrs["date"] is None:
            attrs["date"] = timezone.now()

        # An invoice belongs to the appointment's cabinet, not to the payer's.
        cabinet = self.context.get("cabinet")
        if cabinet is not None and appointment.cabinet_id != cabinet.id:
            raise serializers.ValidationError(
                {"appointment": "Ce rendez-vous n'appartient pas a votre cabinet."}
            )
        return attrs
