from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from core.mixins import CabinetScopedQuerysetMixin
from core.permissions import IsCabinetStaffOrAdmin

from .models import ActeDemander, ActeFait, Medicament
from .serializers import (
    ActeDemanderSerializer,
    ActeFaitSerializer,
    MedicamentSerializer,
)


class MedicamentViewSet(CabinetScopedQuerysetMixin, ModelViewSet):
    queryset = Medicament.objects.select_related("cabinet")
    serializer_class = MedicamentSerializer
    permission_classes = [IsCabinetStaffOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "id"]


class ActeDemanderViewSet(CabinetScopedQuerysetMixin, ModelViewSet):
    queryset = ActeDemander.objects.select_related("cabinet")
    serializer_class = ActeDemanderSerializer
    permission_classes = [IsCabinetStaffOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at", "id"]


class ActeFaitViewSet(CabinetScopedQuerysetMixin, ModelViewSet):
    queryset = ActeFait.objects.select_related("cabinet")
    serializer_class = ActeFaitSerializer
    permission_classes = [IsCabinetStaffOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at", "id"]
