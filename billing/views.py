from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from common.permissions import IsCabinetStaff
from common.viewsets import CabinetScopedViewSet

from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Invoice
        fields = ("appointment", "payed", "amount", "date_from", "date_to")


class InvoiceViewSet(CabinetScopedViewSet):
    """Invoices attached to the caller's cabinet's appointments.

    Scoping goes through `appointment__cabinet`. The old implementation filtered
    `recipient` -- a foreign key to `auth_user` -- against a cabinet id, so the
    endpoint never returned the caller's own invoices.
    """

    queryset = Invoice.objects.select_related(
        "appointment",
        "appointment__patient",
        "recipient",
    ).all()
    serializer_class = InvoiceSerializer
    permission_classes = (IsCabinetStaff,)
    cabinet_field = "appointment__cabinet"
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = InvoiceFilter
    search_fields = ("appointment__patient__firstname", "appointment__patient__lastname")
    ordering_fields = ("date", "amount", "created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["cabinet"] = self.get_cabinet()
        return context

    def perform_create(self, serializer):
        if "cabinet" in serializer.validated_data:
            serializer.validated_data.pop("cabinet")
        serializer.save()

    @action(detail=False, methods=["get"])
    def unpaid(self, request):
        """Outstanding invoices for the caller's cabinet."""
        queryset = self.filter_queryset(self.get_queryset().filter(payed=False))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
