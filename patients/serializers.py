from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from cabinets.models import Cabinet

from .models import Patient, PatientFile

# 5 MB. Documents are scans, not video.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class PatientSerializer(serializers.ModelSerializer):
    cabinet_name = serializers.CharField(source="cabinet.name", read_only=True)
    cabinet = serializers.PrimaryKeyRelatedField(queryset=Cabinet.objects.all(), required=False)

    class Meta:
        model = Patient
        fields = (
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
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
        # Uniqueness is enforced by a per-cabinet DB constraint, so the
        # serializer only checks it when a cabinet is already assigned.
        validators = []

    def validate_age(self, value):
        if value is not None and not 0 <= value <= 130:
            raise serializers.ValidationError("L'age doit etre compris entre 0 et 130.")
        return value

    def validate(self, attrs):
        cabinet = attrs.get("cabinet") or getattr(self.instance, "cabinet", None)
        if cabinet is not None:
            self.assert_unique_in_cabinet(cabinet, attrs)
        return attrs

    @staticmethod
    def assert_unique_in_cabinet(cabinet, attrs, instance=None):
        """`cin` and `phone` are unique within a cabinet, not globally.

        On create the cabinet can be unknown at validation time (it is resolved
        from the caller in `perform_create`), so the view calls this too.
        """
        instance = instance if instance is not None else attrs.get("instance")
        for field in ("cin", "phone"):
            value = attrs.get(field)
            if not value:
                continue
            queryset = Patient.objects.filter(cabinet=cabinet, **{field: value})
            if instance is not None:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {field: f"Un patient de ce cabinet utilise deja cette valeur ({value})."}
                )


class PatientFileSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    # A document is meaningless without knowing whose it is, and the sibling
    # endpoints (appointment, invoice) already resolve the name server side. Doing
    # the same here keeps the list screen from having to fan out one request per
    # row just to label them.
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientFile
        fields = (
            "id",
            "patient",
            "patient_name",
            "file",
            "uploaded_at",
            "uploaded_by",
            "download_url",
        )
        read_only_fields = ("uploaded_at", "uploaded_by", "download_url", "patient_name")

    def get_uploaded_by(self, obj):
        # Not stored: derived from the request at upload time and left out of the
        # schema to avoid coupling this serializer to the request lifecycle.
        return None

    def get_patient_name(self, obj):
        patient = obj.patient
        return " ".join(
            part for part in (patient.firstname, patient.lastname) if part
        ).strip()

    def get_download_url(self, obj):
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def validate_file(self, value):
        if value.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("Le fichier depasse la taille maximale de 5 Mo.")
        return value

    def validate(self, attrs):
        patient = attrs.get("patient") or getattr(self.instance, "patient", None)
        cabinet = self.context.get("cabinet")
        if patient is not None and cabinet is not None and patient.cabinet_id != cabinet.id:
            raise DjangoValidationError("Le patient appartient a un autre cabinet.")
        return attrs
