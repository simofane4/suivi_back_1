from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser

from common.permissions import IsCabinetStaff
from common.viewsets import CabinetScopedViewSet

from .models import Patient, PatientFile
from .serializers import PatientFileSerializer, PatientSerializer


class PatientFilter(filters.FilterSet):
    lastname = filters.CharFilter(lookup_expr="istartswith")
    firstname = filters.CharFilter(lookup_expr="istartswith")
    child = filters.BooleanFilter()

    class Meta:
        model = Patient
        fields = ("cabinet", "gender", "child", "lastname", "firstname", "phone", "cin")


class PatientViewSet(CabinetScopedViewSet):
    """Patients.

    Staff see and create only inside their own cabinet. An admin has no
    cabinet of its own, so it sees every patient and picks one explicitly.
    """

    queryset = Patient.objects.select_related("cabinet").all()
    serializer_class = PatientSerializer
    permission_classes = (IsCabinetStaff,)
    # `search_fields` and `ordering_fields` were declared but never wired to a
    # backend, so `?search=` and `?ordering=` were silently ignored.
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = PatientFilter
    search_fields = ("firstname", "lastname", "cin", "phone")
    ordering_fields = ("created_at", "lastname", "firstname", "age")

    def perform_create(self, serializer):
        # Resolve the cabinet exactly the way the base class does -- staff get
        # their own, an admin gets the one it selected -- but before saving, so
        # a missing cabinet is a clear 400 instead of a NOT NULL 409, and so the
        # per-cabinet uniqueness check can run.
        cabinet = self.get_cabinet_or_raise() or serializer.validated_data.get("cabinet")
        if cabinet is None:
            raise serializers.ValidationError({"cabinet": "Ce champ est obligatoire."})
        PatientSerializer.assert_unique_in_cabinet(cabinet, serializer.validated_data)
        serializer.save(cabinet=cabinet)


class PatientFileViewSet(CabinetScopedViewSet):
    """Documents attached to a patient.

    The `PatientFile` model existed with no endpoint at all, so uploads were
    impossible through the API.
    """

    queryset = PatientFile.objects.select_related("patient", "patient__cabinet").all()
    serializer_class = PatientFileSerializer
    permission_classes = (IsCabinetStaff,)
    parser_classes = (MultiPartParser, FormParser)
    # A file has no cabinet of its own: it belongs to one through its patient.
    cabinet_field = "patient__cabinet"
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ("patient", "uploaded_at")
    search_fields = ("patient__firstname", "patient__lastname", "file")
    ordering_fields = ("uploaded_at",)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["cabinet"] = self.get_cabinet()
        return context
