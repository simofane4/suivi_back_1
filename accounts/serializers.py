from typing import Optional

from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.permissions import ADMIN

from .models import Assistant, Cabinet, Doctor, Specialite, User


class UserSerializer(serializers.ModelSerializer):
    """Shape returned by `/api/auth/me/` and nested inside staff resources."""

    cabinet_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "role",
            "cabinet_id",
        ]
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds `role` and `cabinet_id` claims so the client can gate the UI."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["cabinet_id"] = user.cabinet_id
        return token


class CabinetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cabinet
        fields = ["id", "name", "number", "address", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SpecialiteSerializer(serializers.ModelSerializer):
    """Global catalogue: exposes only the label, without timestamps."""

    class Meta:
        model = Specialite
        fields = ["id", "name"]


class StaffSerializerMixin:
    """Create/update the linked `User` alongside the staff profile."""

    role = None

    def _is_admin(self):
        user = self.context["request"].user
        return bool(user.is_superuser or getattr(user, "role", None) == ADMIN)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Un utilisateur avec ce nom d'utilisateur existe déjà."
            )
        return value

    def create(self, validated_data):
        request = self.context["request"]
        username = validated_data.pop("username")
        password = validated_data.pop("password", None)
        email = validated_data.pop("email", "") or ""
        first_name = validated_data.pop("first_name", "") or ""
        last_name = validated_data.pop("last_name", "") or ""

        cabinet = validated_data.get("cabinet")
        if not self._is_admin():
            cabinet = request.user.cabinet
            validated_data["cabinet"] = cabinet

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=self.role,
            cabinet=cabinet,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        with transaction.atomic():
            user.save()
            validated_data["user"] = user
            return super().create(validated_data)

    def update(self, instance, validated_data):
        user = instance.user
        username = validated_data.pop("username", None)
        if username:
            user.username = username
        for field in ("email", "first_name", "last_name"):
            if field in validated_data:
                setattr(user, field, validated_data.pop(field) or "")
        password = validated_data.pop("password", None)
        if password:
            user.set_password(password)
        if self._is_admin():
            cabinet = validated_data.get("cabinet")
            if cabinet is not None:
                user.cabinet = cabinet
        else:
            validated_data.pop("cabinet", None)
        user.save()
        return super().update(instance, validated_data)


class DoctorSerializer(StaffSerializerMixin, serializers.ModelSerializer):
    role = User.Role.DOCTOR
    user = UserSerializer(read_only=True)
    cabinet_name = serializers.CharField(source="cabinet.name", read_only=True)
    specialiste_name = serializers.SerializerMethodField()
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Doctor
        fields = [
            "id",
            "user",
            "cabinet",
            "cabinet_name",
            "img",
            "inp",
            "gender",
            "phone",
            "address",
            "specialiste",
            "specialiste_name",
            "created_at",
            "updated_at",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_specialiste_name(self, obj) -> Optional[str]:
        return obj.specialiste.name if obj.specialiste else None


class AssistantSerializer(StaffSerializerMixin, serializers.ModelSerializer):
    role = User.Role.ASSISTANT
    user = UserSerializer(read_only=True)
    cabinet_name = serializers.CharField(source="cabinet.name", read_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Assistant
        fields = [
            "id",
            "user",
            "cabinet",
            "cabinet_name",
            "img",
            "cin",
            "gender",
            "phone",
            "address",
            "created_at",
            "updated_at",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
