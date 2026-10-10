from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.models import Cabinet

from .models import ASSURANCE_RATIOS, Invoice, InvoiceItem, Payment, ratio_for_assurance


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["id", "label", "amount"]
        read_only_fields = ["id"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "kind", "method", "note", "paid_at"]
        read_only_fields = ["id", "paid_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    cabinet = serializers.PrimaryKeyRelatedField(
        queryset=Cabinet.objects.all(), required=False
    )
    patient_name = serializers.SerializerMethodField()
    recipient_username = serializers.SerializerMethodField()
    items = InvoiceItemSerializer(many=True, required=False)

    patient_share = serializers.SerializerMethodField()
    organisme_share = serializers.SerializerMethodField()
    patient_paid = serializers.SerializerMethodField()
    organisme_paid = serializers.SerializerMethodField()
    patient_rest = serializers.SerializerMethodField()
    organisme_rest = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "cabinet",
            "appointment",
            "patient_name",
            "date",
            "amount",
            "organisme_ratio",
            "recipient",
            "recipient_username",
            "payed",
            "status",
            "items",
            "patient_share",
            "organisme_share",
            "patient_paid",
            "organisme_paid",
            "patient_rest",
            "organisme_rest",
            "total_paid",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_patient_name(self, obj) -> str:
        return str(obj.patient)

    def get_recipient_username(self, obj) -> str:
        return obj.recipient.username if obj.recipient_id else ""

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_patient_share(self, obj):
        return obj.patient_share

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_organisme_share(self, obj):
        return obj.organisme_share

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_patient_paid(self, obj):
        return obj.patient_paid

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_organisme_paid(self, obj):
        return obj.organisme_paid

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_patient_rest(self, obj):
        return obj.patient_rest

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_organisme_rest(self, obj):
        return obj.organisme_rest

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_total_paid(self, obj):
        return obj.total_paid

    def _is_admin(self):
        user = self.context["request"].user
        return bool(user.is_superuser or getattr(user, "role", None) == "admin")

    def validate(self, attrs):
        amount = attrs.get("amount")
        if amount is not None and amount < 0:
            raise serializers.ValidationError(
                {"amount": "Le montant ne peut pas être négatif."}
            )
        appointment = attrs.get("appointment") or getattr(
            self.instance, "appointment", None
        )
        if appointment is None:
            return attrs
        if not self._is_admin():
            user = self.context["request"].user
            if appointment.cabinet_id != user.cabinet_id:
                raise serializers.ValidationError(
                    {"appointment": "Le rendez-vous n'appartient pas à votre cabinet."}
                )
        return attrs

    def _default_ratio(self, appointment):
        if appointment is None:
            return Decimal("0")
        return ratio_for_assurance(appointment.patient.assurance)

    def _rebuild_items(self, invoice, items):
        invoice.items.all().delete()
        for item in items:
            InvoiceItem.objects.create(invoice=invoice, **item)

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        appointment = validated_data.get("appointment")
        user = self.context["request"].user
        if not self._is_admin():
            validated_data["cabinet"] = user.cabinet
        if "organisme_ratio" not in validated_data:
            validated_data["organisme_ratio"] = self._default_ratio(appointment)
        if "recipient" not in validated_data:
            validated_data["recipient"] = user
        invoice = Invoice.objects.create(**validated_data)
        self._rebuild_items(invoice, items)
        return invoice

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        payed = validated_data.pop("payed", None)
        if not self._is_admin():
            validated_data.pop("cabinet", None)
        invoice = super().update(instance, validated_data)
        if items is not None:
            self._rebuild_items(invoice, items)
        if payed is not None:
            invoice.status = (
                Invoice.Status.PAID if payed else Invoice.Status.UNPAID
            )
            invoice.payed = payed
            invoice.save(update_fields=["status", "payed", "updated_at"])
        return invoice