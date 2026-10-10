from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from common.permissions import IsAdminOrReadOnly
from common.tenancy import StaffCabinetMixin
from common.viewsets import GlobalViewSet

from .models import Cabinet, Specialite
from .serializers import CabinetSerializer, SpecialiteSerializer


class CabinetViewSet(StaffCabinetMixin, viewsets.ModelViewSet):
    """Cabinets.

    Any staff member can read; only an admin can create, modify or delete one.
    A non-admin sees just their own clinic.
    """

    queryset = Cabinet.objects.all()
    serializer_class = CabinetSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("name", "number", "address")
    ordering_fields = ("name", "created_at")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.get_staff_role() == "admin":
            return queryset
        cabinet = self.get_cabinet()
        return queryset.filter(pk=cabinet.pk) if cabinet else queryset.none()


class SpecialiteViewSet(GlobalViewSet):
    """Medical specialities.

    Global reference data shared by every cabinet, so it is not cabinet-scoped.
    Readable by any authenticated user, writable by an admin only.
    """

    queryset = Specialite.objects.all()
    serializer_class = SpecialiteSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("name",)
    ordering_fields = ("name",)
