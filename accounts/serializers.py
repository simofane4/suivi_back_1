from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from cabinets.models import Cabinet, Specialite

from .models import Assistant, Doctor


class UserSummarySerializer(serializers.ModelSerializer):
    """Compact view of the auth account behind a staff member."""

    role = serializers.SerializerMethodField()
    cabinet_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "role",
            "cabinet_id",
        )

    def get_role(self, obj) -> str | None:
        # The reverse one-to-one accessors exist only once the profile does.
        if hasattr(obj, "doctor"):
            return "doctor"
        if hasattr(obj, "assistant"):
            return "assistant"
        return "admin" if obj.is_superuser else None

    def get_cabinet_id(self, obj):
        if hasattr(obj, "doctor"):
            return obj.doctor.cabinet_id
        if hasattr(obj, "assistant"):
            return obj.assistant.cabinet_id
        return None


class _StaffWriteMixin:
    """Fields describing the auth account, accepted on create and update."""

    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            user = getattr(self.instance, "user", None)
            queryset = queryset.exclude(pk=user.pk if user else None)
        if queryset.exists():
            raise serializers.ValidationError("Cette adresse email est deja utilisee.")
        return value


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    cabinet_name = serializers.CharField(source="cabinet.name", read_only=True)
    specialiste_name = serializers.CharField(source="specialiste.name", read_only=True)

    class Meta:
        model = Doctor
        fields = (
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
        )
        read_only_fields = ("created_at", "updated_at")


class DoctorCreateSerializer(serializers.ModelSerializer):
    """Creates the `User` account and the `Doctor` profile together.

    The previous implementation created the user, then fetched it again with
    `User.objects.last()`, which attaches the wrong account under concurrency.
    Here the instance returned by `create_user` is used directly, inside one
    transaction.
    """

    username = serializers.CharField(max_length=150, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    email = serializers.EmailField(required=True, write_only=True)
    first_name = serializers.CharField(max_length=150, required=True, write_only=True)
    last_name = serializers.CharField(max_length=150, required=True, write_only=True)
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all())
    specialiste = serializers.PrimaryKeyRelatedField(queryset=Specialite.objects.all())

    class Meta:
        model = Doctor
        fields = (
            "id",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "cabinet",
            "img",
            "inp",
            "gender",
            "phone",
            "address",
            "specialiste",
        )

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        if queryset.exists():
            raise serializers.ValidationError("Cette adresse email est deja utilisee.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        user_data = {
            "username": validated_data.pop("username"),
            "email": validated_data.pop("email"),
            "first_name": validated_data.pop("first_name"),
            "last_name": validated_data.pop("last_name"),
        }
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **user_data)
        return Doctor.objects.create(user=user, **validated_data)

    def to_representation(self, instance):
        return DoctorSerializer(instance, context=self.context).data


class DoctorUpdateSerializer(serializers.ModelSerializer):
    """Partial update of a doctor, including their auth account."""

    email = serializers.EmailField(required=False, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, write_only=True)
    last_name = serializers.CharField(max_length=150, required=False, write_only=True)

    class Meta:
        model = Doctor
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "cabinet",
            "img",
            "inp",
            "gender",
            "phone",
            "address",
            "specialiste",
        )

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        user = getattr(self.instance, "user", None)
        if user:
            queryset = queryset.exclude(pk=user.pk)
        if queryset.exists():
            raise serializers.ValidationError("Cette adresse email est deja utilisee.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user
        for field in ("email", "first_name", "last_name"):
            if field in validated_data:
                setattr(user, field, validated_data.pop(field))
        user.save()
        return super().update(instance, validated_data)


class AssistantSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    cabinet_name = serializers.CharField(source="cabinet.name", read_only=True)

    class Meta:
        model = Assistant
        fields = (
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
        )
        read_only_fields = ("created_at", "updated_at")


class AssistantCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    email = serializers.EmailField(required=True, write_only=True)
    first_name = serializers.CharField(max_length=150, required=True, write_only=True)
    last_name = serializers.CharField(max_length=150, required=True, write_only=True)
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all())

    class Meta:
        model = Assistant
        fields = (
            "id",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "cabinet",
            "img",
            "cin",
            "gender",
            "phone",
            "address",
        )

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        if queryset.exists():
            raise serializers.ValidationError("Cette adresse email est deja utilisee.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        user_data = {
            "username": validated_data.pop("username"),
            "email": validated_data.pop("email"),
            "first_name": validated_data.pop("first_name"),
            "last_name": validated_data.pop("last_name"),
        }
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **user_data)
        return Assistant.objects.create(user=user, **validated_data)

    def to_representation(self, instance):
        return AssistantSerializer(instance, context=self.context).data


class AssistantUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, write_only=True)
    last_name = serializers.CharField(max_length=150, required=False, write_only=True)

    class Meta:
        model = Assistant
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "cabinet",
            "img",
            "cin",
            "gender",
            "phone",
            "address",
        )

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        user = getattr(self.instance, "user", None)
        if user:
            queryset = queryset.exclude(pk=user.pk)
        if queryset.exists():
            raise serializers.ValidationError("Cette adresse email est deja utilisee.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user
        for field in ("email", "first_name", "last_name"):
            if field in validated_data:
                setattr(user, field, validated_data.pop(field))
        user.save()
        return super().update(instance, validated_data)
