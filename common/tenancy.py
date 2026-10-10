"""Resolving which cabinet a request belongs to.

The old code repeated this block in a dozen views:

    try:
        data['cabinet'] = request.user.doctor.cabinet.id
    except User.related_field.RelatedObjectDoesNotExist:
        data['cabinet'] = request.user.assistant.cabinet.id

`User.related_field.RelatedObjectDoesNotExist` is not a real exception, so the
fallback never fired and any assistant-only request raised `AttributeError`.
Accessing the reverse one-to-one relation directly has the same shape of
problem. `resolve_cabinet` here is the single implementation.

Deliberately avoids importing any app's models at module scope: app permissions
import this module, so a model import here would be circular.
"""

from rest_framework.exceptions import PermissionDenied

ROLE_DOCTOR = "doctor"
ROLE_ASSISTANT = "assistant"
ROLE_ADMIN = "admin"


class StaffCabinetMixin:
    """Adds role/cabinet resolution to a view or serializer."""

    @property
    def user(self):
        return getattr(self, "request", None) and self.request.user

    def get_staff_role(self) -> str | None:
        user = self.user
        if user is None or not user.is_authenticated:
            return None
        if user.is_superuser or user.is_staff:
            return ROLE_ADMIN
        # Reverse one-to-one accessors, set by `related_name` on Doctor/Assistant.
        if hasattr(user, "doctor"):
            return ROLE_DOCTOR
        if hasattr(user, "assistant"):
            return ROLE_ASSISTANT
        return None

    def get_cabinet(self):
        """Return the caller's Cabinet, or None for admins with no single cabinet."""
        user = self.user
        if user is None or not user.is_authenticated:
            return None
        if hasattr(user, "doctor"):
            return user.doctor.cabinet
        if hasattr(user, "assistant"):
            return user.assistant.cabinet
        return None

    def get_cabinet_or_raise(self):
        cabinet = self.get_cabinet()
        if cabinet is None and not self.get_staff_role() == ROLE_ADMIN:
            raise PermissionDenied("No cabinet is associated with this account.")
        return cabinet
