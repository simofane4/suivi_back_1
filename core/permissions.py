from rest_framework.permissions import BasePermission

ADMIN = "admin"
DOCTOR = "doctor"
ASSISTANT = "assistant"
PATIENT = "patient"


def user_role(user) -> str:
    return getattr(user, "role", None)


class IsAdmin(BasePermission):
    """Full access for the administrator, or a Django superuser."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return user.is_superuser or user_role(user) == ADMIN


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user_role(user) == DOCTOR)


class IsCabinetStaff(BasePermission):
    """A doctor or an assistant, i.e. anyone attached to a cabinet."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user_role(user) in {DOCTOR, ASSISTANT}
        )


class IsCabinetStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return user.is_superuser or user_role(user) in {ADMIN, DOCTOR, ASSISTANT}
