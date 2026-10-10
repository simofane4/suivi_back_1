from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from core.mixins import CabinetScopedQuerysetMixin
from core.permissions import IsCabinetStaffOrAdmin

from .models import Allergie, Antecedent, Observation, Patient, PatientFile
from .serializers import (
    AllergieSerializer,
    AntecedentSerializer,
    ObservationSerializer,
    PatientFileSerializer,
    PatientSerializer,
)


class PatientViewSet(CabinetScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Patient.objects.select_related("cabinet")
    serializer_class = PatientSerializer
    permission_classes = [IsCabinetStaffOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["firstname", "lastname", "cin", "phone", "numero_adherent"]
    ordering_fields = ["lastname", "firstname", "age", "created_at", "id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        for param, field in (
            ("cabinet", "cabinet_id"),
            ("gender", "gender"),
            ("child", "child"),
            ("lastname", "lastname"),
            ("firstname", "firstname"),
            ("cin", "cin"),
            ("phone", "phone"),
        ):
            value = params.get(param)
            if value not in (None, ""):
                queryset = queryset.filter(**{field: value})
        return queryset

    @extend_schema(
        responses={
            200: inline_serializer(
                "PatientDossier",
                fields={
                    "patient": PatientSerializer(),
                    "antecedents": AntecedentSerializer(many=True),
                    "allergies": AllergieSerializer(many=True),
                    "observations": ObservationSerializer(many=True),
                },
            )
        }
    )
    @action(detail=True, methods=["get"])
    def dossier(self, request, pk=None):
        """Aggregates a patient's medical record in one call."""
        patient = self.get_object()
        return Response(
            {
                "patient": PatientSerializer(patient, context=self.get_serializer_context()).data,
                "antecedents": AntecedentSerializer(
                    patient.antecedents.all(), many=True, context=self.get_serializer_context()
                ).data,
                "allergies": AllergieSerializer(
                    patient.allergies.all(), many=True, context=self.get_serializer_context()
                ).data,
                "observations": ObservationSerializer(
                    patient.observations.all(), many=True, context=self.get_serializer_context()
                ).data,
            }
        )


class PatientFileViewSet(CabinetScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = PatientFile.objects.select_related("patient__cabinet")
    serializer_class = PatientFileSerializer
    permission_classes = [IsCabinetStaffOrAdmin]
    cabinet_field = "patient__cabinet"
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["patient__firstname", "patient__lastname", "file"]
    ordering_fields = ["uploaded_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        patient = self.request.query_params.get("patient")
        if patient not in (None, ""):
            queryset = queryset.filter(patient_id=patient)
        return queryset


class _MedicalRecordViewSet(CabinetScopedQuerysetMixin, viewsets.ModelViewSet):
    """Base for note-like models, scoped through the owning patient's cabinet."""

    permission_classes = [IsCabinetStaffOrAdmin]
    cabinet_field = "patient__cabinet"

    def get_queryset(self):
        queryset = super().get_queryset()
        patient = self.request.query_params.get("patient")
        if patient not in (None, ""):
            queryset = queryset.filter(patient_id=patient)
        return queryset


class AntecedentViewSet(_MedicalRecordViewSet):
    queryset = Antecedent.objects.select_related("patient__cabinet")
    serializer_class = AntecedentSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["label", "notes"]
    ordering_fields = ["created_at", "id"]


class AllergieViewSet(_MedicalRecordViewSet):
    queryset = Allergie.objects.select_related("patient__cabinet")
    serializer_class = AllergieSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "severity"]
    ordering_fields = ["created_at", "id"]


class ObservationViewSet(_MedicalRecordViewSet):
    queryset = Observation.objects.select_related("patient__cabinet", "created_by")
    serializer_class = ObservationSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["diagnostic", "diagnostic_label", "notes"]
    ordering_fields = ["created_at", "diagnostic", "version"]

    def perform_create(self, serializer):
        serializer.save(version=1, created_by=self.request.user)