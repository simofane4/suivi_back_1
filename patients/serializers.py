from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from accounts.models import Cabinet
from core.permissions import ADMIN

from .models import Allergie, Antecedent, Observation, Patient, PatientFile

MAX_FILE_SIZE = 5 * 1024 * 1024


class PatientSerializer(serializers.ModelSerializer):
    """Read/write shape for `/api/patients/`."""

    cabinet_name = serializers.CharField(source="cabinet.name", read_only=True)
    cabinet = serializers.PrimaryKeyRelatedField(
        queryset=Cabinet.objects.all(), required=False
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "cabinet",
            "cabinet_name",
            "cin",
            "img",
            "firstname",
            "lastname",
            "gender",
            "age",
            "phone",
            "address",
            "child",
            "assurance",
            "numero_adherent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_unique_together_validators(self):
        # Cabinet is optional for staff (resolved from the token), so the
        # constraint-driven validator cannot require it. Uniqueness of
        # (cabinet, id_number) is enforced manually in `_ensure_unique_cin`
        # while the DB column keeps its dedicated constraint.
        return []

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        if not (user.is_superuser or getattr(user, "role", None) == ADMIN):
            validated_data["cabinet"] = user.cabinet
        self._ensure_unique_cin(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not (user.is_superuser or getattr(user, "role", None) == ADMIN):
            validated_data.pop("cabinet", None)
        validated_data["cabinet"] = instance.cabinet
        self._ensure_unique_cin(validated_data, exclude_id=instance.id)
        return super().update(instance, validated_data)

    def _ensure_unique_cin(self, data, exclude_id=None):
        cabinet = data.get("cabinet")
        queryset = Patient.objects.filter(cabinet=cabinet, cin=data.get("cin"))
        if exclude_id is not None:
            queryset = queryset.exclude(pk=exclude_id)
        if queryset.exists():
            raise serializers.ValidationError(
                {"cin": "Un patient avec ce CIN existe déjà dans ce cabinet."}
            )


class PatientFileSerializer(serializers.ModelSerializer):
    """Read/write shape for `/api/patient-files/` (multipart)."""

    patient_name = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = PatientFile
        fields = [
            "id",
            "patient",
            "patient_name",
            "file",
            "uploaded_at",
            "uploaded_by",
            "download_url",
        ]
        read_only_fields = ["id", "uploaded_at"]

    def validate_file(self, value):
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                "Le fichier dépasse la taille maximale de 5 Mo."
            )
        return value

    def validate_patient(self, value):
        user = self.context["request"].user
        if not (user.is_superuser or getattr(user, "role", None) == ADMIN):
            if value.cabinet_id != user.cabinet_id:
                raise serializers.ValidationError(
                    "Le patient n'appartient pas à votre cabinet."
                )
        return value

    def update(self, instance, validated_data):
        validated_data.pop("patient", None)
        return super().update(instance, validated_data)

    def get_patient_name(self, obj) -> str:
        return str(obj.patient)

    def get_download_url(self, obj) -> str | None:
        request = self.context.get("request")
        if request is None or not obj.file:
            return None
        try:
            return request.build_absolute_uri(obj.file.url)
        except ValueError:
            return None

    @extend_schema_field(str)
    def get_uploaded_by(self, obj) -> None:
        return None


class AntecedentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Antecedent
        fields = ["id", "patient", "label", "notes", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AllergieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergie
        fields = ["id", "patient", "name", "severity", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ObservationSerializer(serializers.ModelSerializer):
    created_by = serializers.IntegerField(source="created_by_id", read_only=True)

    class Meta:
        model = Observation
        fields = [
            "id",
            "patient",
            "diagnostic",
            "diagnostic_label",
            "notes",
            "version",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "version", "created_by", "created_at", "updated_at"]