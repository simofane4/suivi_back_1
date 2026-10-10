"""Base viewsets."""

from rest_framework import viewsets

from common.permissions import CabinetScopedMixin
from common.tenancy import StaffCabinetMixin


class BaseModelViewSet(StaffCabinetMixin, viewsets.ModelViewSet):
    """CRUD for a model owned by a cabinet, scoped to the caller's cabinet."""

    pass


class CabinetScopedViewSet(CabinetScopedMixin, BaseModelViewSet):
    pass


class GlobalViewSet(StaffCabinetMixin, viewsets.ModelViewSet):
    """For reference data that is shared across every cabinet."""

    pass
