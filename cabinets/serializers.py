from rest_framework import serializers

from .models import Cabinet, Specialite


class CabinetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cabinet
        fields = ("id", "name", "number", "address", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class SpecialiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialite
        fields = ("id", "name")
