"""Permissions and queryset scoping.

Before this rewrite every view used only `IsAuthenticated`, so any logged-in
user could list, read, update and delete every other clinic's patients,
appointments and invoices. `CabinetScopedMixin` narrows each queryset to the
caller's own cabinet; admins keep cross-cabinet visibility.
"""

from django.core.exceptions import FieldDoesNotExist
from rest_framework import permissions, serializers

from common.tenancy import ROLE_ADMIN, ROLE_ASSISTANT, ROLE_DOCTOR


class IsDoctor(permissions.BasePermission):
    """Only a doctor account."""

    def has_permission(self, request, view):
        return view.get_staff_role() == ROLE_DOCTOR


class IsCabinetStaff(permissions.BasePermission):
    """Any doctor or assistant of a cabinet, or an admin."""

    def has_permission(self, request, view):
        role = view.get_staff_role()
        return role in {ROLE_DOCTOR, ROLE_ASSISTANT, ROLE_ADMIN}


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.get_staff_role() == ROLE_ADMIN


class IsAdminOrReadOnly(permissions.BasePermission):
    """Global reference data (specialities, cabinets) is readable by staff but
    only writable by an admin."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(view.get_staff_role())
        return view.get_staff_role() == ROLE_ADMIN


class CabinetScopedMixin:
    """Filter `get_queryset` down to the caller's cabinet.

    Set `cabinet_field` on the view to the path from this model to its cabinet,
    or override `scope_queryset` when the relation is not a simple field.
    """

    cabinet_field = "cabinet"

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.scope_queryset(queryset)

    def scope_queryset(self, queryset):
        if self.get_staff_role() == ROLE_ADMIN:
            return queryset
        cabinet = self.get_cabinet()
        if cabinet is None:
            # Authenticated but attached to no clinic: see nothing.
            return queryset.none()
        return queryset.filter(**{self.cabinet_field: cabinet})

    def requires_cabinet(self, serializer) -> bool:
        """True when a record cannot exist without an owning cabinet.

        The serializers declare `cabinet` as `required=False` so that staff may
        omit it and have their own forced in, which leaves nothing in the field
        itself to catch an admin who forgets it. Fall back to the column: a
        non-null cabinet has to come from the payload when there is no token one.
        """
        field = serializer.fields.get("cabinet")
        if field is None or field.read_only:
            return False
        try:
            model_field = serializer.Meta.model._meta.get_field(self.cabinet_field)
        except FieldDoesNotExist:
            return False
        return not model_field.null

    def perform_create(self, serializer):
        # Staff are locked into their own cabinet. An admin is attached to none,
        # so overwriting unconditionally wrote `cabinet=None` and every admin
        # create failed with an opaque 409. An admin picks the cabinet instead.
        cabinet = self.get_cabinet_or_raise()
        if "cabinet" not in serializer.fields:
            # The model has no cabinet of its own -- a patient file belongs to
            # one through its patient, which the serializer validates -- so
            # there is nothing for this mixin to force.
            serializer.save()
            return
        if cabinet is None:
            if self.requires_cabinet(serializer) and "cabinet" not in serializer.validated_data:
                # Checking here turns the IntegrityError that `save()` would
                # raise into the 400 the client can act on.
                raise serializers.ValidationError({"cabinet": "Ce champ est obligatoire."})
            serializer.save()
            return
        serializer.save(cabinet=cabinet)

    def perform_update(self, serializer):
        # The owning cabinet is part of the tenancy, not editable data: a staff
        # member must not be able to PATCH a record into somebody else's clinic.
        cabinet = self.get_cabinet()
        if cabinet is None or "cabinet" not in serializer.fields:
            # Either an admin (keep the stored cabinet unless the payload moved
            # it) or a model with no cabinet of its own -- an invoice belongs to
            # a cabinet through its appointment, so there is nothing to force.
            serializer.save()
            return
        serializer.save(cabinet=cabinet)
