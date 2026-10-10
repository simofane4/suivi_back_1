from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from common.permissions import IsCabinetStaff
from common.viewsets import CabinetScopedViewSet

from .models import ActeDemander, ActeFait, Appointment, Medicament, Ordonnance
from .serializers import (
    ActeDemanderSerializer,
    ActeFaitSerializer,
    AppointmentSerializer,
    MedicamentSerializer,
    OrdonnanceSerializer,
)


class ActeDemanderFilter(filters.FilterSet):
    class Meta:
        model = ActeDemander
        fields = ("cabinet", "title")


class ActeDemanderViewSet(CabinetScopedViewSet):
    queryset = ActeDemander.objects.select_related("cabinet").all()
    serializer_class = ActeDemanderSerializer
    permission_classes = (IsCabinetStaff,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = ActeDemanderFilter
    search_fields = ("title", "description")
    ordering_fields = ("title", "created_at")


class ActeFaitViewSet(CabinetScopedViewSet):
    queryset = ActeFait.objects.select_related("cabinet").all()
    serializer_class = ActeFaitSerializer
    permission_classes = (IsCabinetStaff,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ("title", "description")
    ordering_fields = ("title", "created_at")


class MedicamentViewSet(CabinetScopedViewSet):
    queryset = Medicament.objects.select_related("cabinet").all()
    serializer_class = MedicamentSerializer
    permission_classes = (IsCabinetStaff,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ("name", "description")
    ordering_fields = ("name", "created_at")


class AppointmentFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Appointment
        fields = ("cabinet", "patient", "date", "payed", "date_from", "date_to")


class AppointmentViewSet(CabinetScopedViewSet):
    """Appointments of the caller's cabinet.

    Overlap detection runs in `AppointmentSerializer.validate`, so it returns a
    400 with the conflicting range instead of the previous 201.
    """

    queryset = Appointment.objects.select_related("patient", "cabinet").all()
    serializer_class = AppointmentSerializer
    permission_classes = (IsCabinetStaff,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = AppointmentFilter
    search_fields = ("patient__firstname", "patient__lastname", "description")
    ordering_fields = ("date", "start", "created_at")


class OrdonnanceViewSet(CabinetScopedViewSet):
    queryset = Ordonnance.objects.select_related("cabinet", "appointment").prefetch_related(
        "medicaments",
    )
    serializer_class = OrdonnanceSerializer
    permission_classes = (IsCabinetStaff,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ("description", "appointment__patient__lastname")
    ordering_fields = ("created_at",)
