from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from core.mixins import CabinetScopedQuerysetMixin
from core.permissions import IsCabinetStaffOrAdmin

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(CabinetScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related("cabinet", "patient", "doctor__user")
    serializer_class = AppointmentSerializer
    permission_classes = [IsCabinetStaffOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["patient__firstname", "patient__lastname", "reason"]
    ordering_fields = ["date", "start", "created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        date = params.get("date", "").strip()
        if date:
            queryset = queryset.filter(date=date)
        date_from = params.get("date_from", "").strip()
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        date_to = params.get("date_to", "").strip()
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        for param, field in (
            ("cabinet", "cabinet_id"),
            ("patient", "patient_id"),
            ("doctor", "doctor_id"),
            ("status", "status"),
        ):
            value = params.get(param, "").strip()
            if value:
                queryset = queryset.filter(**{field: value})

        payed = params.get("payed", "").strip().lower()
        if payed in ("1", "true", "yes", "0", "false", "no"):
            queryset = queryset.filter(payed=payed in ("1", "true", "yes"))
        return queryset

    @action(detail=False, methods=["get"])
    def agenda(self, request):
        """Un jour donne pour un praticien : la vue calendaire."""
        date = request.query_params.get("date", "").strip()
        praticien = request.query_params.get("praticien", "").strip()
        queryset = self.get_queryset()
        if date:
            queryset = queryset.filter(date=date)
        if praticien:
            queryset = queryset.filter(doctor_id=praticien)
        queryset = queryset.order_by("start")
        return Response(
            self.get_serializer(queryset, many=True).data,
        )