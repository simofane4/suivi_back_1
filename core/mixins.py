from core.permissions import ADMIN


class CabinetScopedQuerysetMixin:
    """Restricts a viewset's queryset to the caller's cabinet.

    Administrators (and superusers) see every row; staff are limited to their
    own cabinet. Set `cabinet_field` when the model does not own a `cabinet`
    column directly (e.g. invoice reaching it through its appointment).
    """

    cabinet_field = "cabinet"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_superuser", False) or getattr(user, "role", None) == ADMIN:
            return queryset
        cabinet_id = getattr(user, "cabinet_id", None)
        if cabinet_id is None:
            return queryset.none()
        return queryset.filter(**{self.cabinet_field: cabinet_id})
